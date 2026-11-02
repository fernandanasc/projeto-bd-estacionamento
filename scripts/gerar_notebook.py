"""Gera o notebook do Colab e os arquivos .sql do projeto a partir de uma única fonte.

Saídas:
- estacionamento_hospitalar.ipynb
- sql/01_criar_bd.sql, sql/02_popular_bd.sql, sql/03_consultas.sql, sql/04_testes_restricoes.sql

Uso: py gerar_notebook.py
"""
import json
import os
import re

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.join(AQUI, "..")

# Cada passo é (tipo, conteúdo, arquivo .sql de destino ou None)
#   md       -> célula de texto
#   sql      -> célula %%bash com posql -c "..." (e vai para o arquivo .sql)
#   sql_erro -> igual, mas o comando DEVE falhar (demonstração de restrição)
#   bash     -> célula de comandos (!...)
passos = []


def md(texto):
    passos.append(("md", texto.strip("\n"), None))


def sql(comando, arquivo):
    passos.append(("sql", comando.strip("\n"), arquivo))


def sql_erro(comando, comentario):
    passos.append(("sql_erro", (comando.strip("\n"), comentario), "04_testes_restricoes.sql"))


def bash(comando):
    passos.append(("bash", comando.strip("\n"), None))


CRIAR = "01_criar_bd.sql"
POPULAR = "02_popular_bd.sql"
CONSULTAS = "03_consultas.sql"

# =====================================================================
md("""
# Sistema de Estacionamento Hospitalar – Projeto de BD (Iteração 2)

**IMD0401 – Banco de Dados – T02 (2026.2)** · Docente: Gustavo Alves Bezerra
Discente: Fernanda Vitoria Silva Do Nascimento

Este notebook **cria**, **popula** e **usa** o banco de dados do estacionamento de um hospital.

**Minimundo (resumo)**
- **Avulso (uso diário):** pega um cartão na entrada, paga o tempo de permanência na saída e devolve o cartão na máquina. Não é cadastrado como pessoa; fica registrado o veículo e a estadia.
- **Mensalista (cliente):** cadastrado com nome, CPF, telefones e endereço. Tem cartão pessoal (a máquina devolve o cartão na saída) e paga **mensalidade**.
- **Categoria isenta:** ambulâncias e veículos médicos não pagam.
- Toda entrada e saída é registrada em uma **estadia**, com a guarita usada.

**Roteiro**
1. Instalação do PostgreSQL
2. Criação do banco (tipos, tabelas e restrições)
3. População com dados de exemplo
4. Testes das restrições
5. Consultas (exemplos de utilização)

O DER está em `diagramas/der_v2.png` e o modelo lógico em `diagramas/dbdiagram_v2.dbml`.
""")

# =====================================================================
md("""
## 1. Instalação do PostgreSQL

Mesmo procedimento das aulas: instalar o PostgreSQL na máquina do Colab.
""")
bash("""
# instalação do postgresql na máquina do colab (saída escondida para não poluir o notebook)
!sudo apt update -qq > /dev/null 2>&1
!sudo apt install -y -qq postgresql postgresql-contrib > /dev/null 2>&1
""")
md("Verificar se foi instalado corretamente e iniciar o servidor.")
bash("""
!psql --version
!sudo service postgresql start
!sudo service postgresql status
""")
md("Criar o banco de dados `estacionamento`.")
bash("!sudo -u postgres createdb estacionamento")
md("O Colab usa o horário UTC. Ajustamos o banco para o fuso de Natal, para que `NOW()` mostre a hora local.")
bash("""!sudo -u postgres psql -c "ALTER DATABASE estacionamento SET TIMEZONE TO 'America/Fortaleza'" """)
md("""
Criar o comando `posql`, como nas aulas, já apontando para o banco `estacionamento`.

- `-d estacionamento`: sempre conecta no nosso banco
- `-P pager=off`: desliga o paginador, então não precisa digitar `\\q`
""")
bash("""
!echo '#!/bin/bash' > /usr/local/bin/posql
!echo 'sudo -u postgres psql -d estacionamento -P pager=off "$@"' >> /usr/local/bin/posql
!chmod +x /usr/local/bin/posql
!posql -c "SELECT CURRENT_DATABASE();"
""")

# =====================================================================
md("""
## 2. Criação do banco

### Do DER para as tabelas

| No DER | No PostgreSQL |
|---|---|
| Atributo chave | `PRIMARY KEY` |
| Atributo composto (`endereco`) | `CREATE TYPE ... AS (...)` |
| Atributo multivalorado (`telefone`) | array `TEXT[]` |
| Atributo derivado (`status`, `tempo_permanencia`) | não é guardado; é calculado na consulta (`VIEW`) |
| Domínio restrito (`tipo`, `status`, `forma_pagamento`) | `CREATE TYPE ... AS ENUM` |
| Relacionamento 1:N | chave estrangeira (`REFERENCES`) do lado N |
| Relacionamento 1:1 | chave estrangeira com `UNIQUE` |
| Participação total | chave estrangeira `NOT NULL` |
| Participação parcial | chave estrangeira que aceita `NULL` |

### 2.1 Tipos

**Atributo composto:** o endereço é formado por logradouro, número, bairro, cidade, UF e CEP. Como visto em aula, isso vira um tipo novo (parecido com um `struct` do C).
""")
sql("""
CREATE TYPE endereco AS (
  logradouro TEXT,
  numero INTEGER,
  bairro TEXT,
  cidade TEXT,
  uf CHAR(2),
  cep CHAR(8)
);
""", CRIAR)
md("""
**Domínios restritos:** o tipo e o status do cartão e a forma de pagamento só podem assumir alguns valores. Usamos `ENUM`, como no exemplo do tipo sanguíneo visto em aula.
""")
sql("""
CREATE TYPE tipo_cartao AS ENUM ('MENSALISTA', 'AVULSO');
CREATE TYPE status_cartao AS ENUM ('ATIVO', 'BLOQUEADO', 'PERDIDO');
CREATE TYPE forma_pagamento AS ENUM ('DINHEIRO', 'CARTAO', 'PIX');
""", CRIAR)
bash('!posql -c "\\dT"')

md("""
### 2.2 Tabelas de classificação dos veículos

Criadas primeiro porque as outras tabelas fazem referência a elas.

- **FABRICANTE (1) – FABRICA – (N) MODELO:** todo modelo tem fabricante (participação total), então `cod_fabricante` é `NOT NULL`.
- **CATEGORIA:** o atributo `isenta` indica os veículos hospitalares e médicos, que não pagam.
""")
sql("""
CREATE TABLE fabricante (
  cod_fabricante SERIAL PRIMARY KEY,
  nome_fabricante TEXT NOT NULL UNIQUE
);

CREATE TABLE modelo (
  cod_modelo SERIAL PRIMARY KEY,
  nome_modelo TEXT NOT NULL,
  cod_fabricante INTEGER NOT NULL REFERENCES fabricante(cod_fabricante)
);

CREATE TABLE categoria (
  cod_categoria SERIAL PRIMARY KEY,
  descricao TEXT NOT NULL UNIQUE,
  isenta BOOLEAN NOT NULL DEFAULT FALSE
);
""", CRIAR)

md("""
### 2.3 Cliente (mensalista)

- `telefone TEXT[]`: multivalorado, um cliente pode ter vários telefones.
- `endereco endereco`: composto, usa o tipo criado acima.
- `CHECK` no CPF: exatamente 11 dígitos.
""")
sql("""
CREATE TABLE cliente (
  cod_cliente SERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  cpf CHAR(11) NOT NULL UNIQUE CHECK (cpf ~ '^[0-9]{11}$'),
  telefone TEXT[],
  endereco endereco
);
""", CRIAR)

md("""
### 2.4 Veículo

- A **placa** é a chave natural. O `CHECK` aceita o padrão antigo (`ABC1234`) e o Mercosul (`ABC1D23`).
- **MODELO – INSTANCIA – VEICULO** e **CATEGORIA – CLASSIFICA – VEICULO:** participação total, então `NOT NULL`.
- **CLIENTE – POSSUI – VEICULO:** participação parcial dos dois lados (o veículo avulso não tem dono cadastrado), então `cod_cliente` aceita `NULL`.
""")
sql("""
CREATE TABLE veiculo (
  placa CHAR(7) PRIMARY KEY CHECK (placa ~ '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$'),
  cor TEXT,
  ano SMALLINT CHECK (ano BETWEEN 1950 AND 2030),
  cod_modelo INTEGER NOT NULL REFERENCES modelo(cod_modelo),
  cod_categoria INTEGER NOT NULL REFERENCES categoria(cod_categoria),
  cod_cliente INTEGER REFERENCES cliente(cod_cliente)
);
""", CRIAR)

md("""
### 2.5 Cartão de acesso

**CLIENTE – RECEBE – CARTAO_ACESSO** é parcial dos dois lados, porque o cartão avulso não tem dono. Para garantir a regra do minimundo, usamos um `CHECK`:

- cartão **MENSALISTA** precisa ter cliente e data de validade;
- cartão **AVULSO** não pode ter cliente nem validade.
""")
sql("""
CREATE TABLE cartao_acesso (
  num_cartao INTEGER PRIMARY KEY,
  tipo tipo_cartao NOT NULL,
  status status_cartao NOT NULL DEFAULT 'ATIVO',
  data_emissao DATE NOT NULL,
  data_validade DATE,
  cod_cliente INTEGER REFERENCES cliente(cod_cliente),
  CONSTRAINT cartao_tipo_cliente CHECK (
    (tipo = 'MENSALISTA' AND cod_cliente IS NOT NULL AND data_validade IS NOT NULL)
    OR
    (tipo = 'AVULSO' AND cod_cliente IS NULL AND data_validade IS NULL)
  ),
  CONSTRAINT validade_depois_emissao CHECK (data_validade > data_emissao)
);
""", CRIAR)

md("### 2.6 Guarita")
sql("""
CREATE TABLE guarita (
  cod_guarita SERIAL PRIMARY KEY,
  localizacao TEXT NOT NULL
);
""", CRIAR)

md("""
### 2.7 Estadia

Cada entrada no pátio gera uma estadia.

- **UTILIZA** (cartão), **REALIZA** (veículo) e **REGISTRA_ENTRADA** (guarita): participação total, então `NOT NULL`.
- **REGISTRA_SAIDA:** parcial, porque enquanto o veículo está no pátio a saída fica vazia.
- Entre **GUARITA** e **ESTADIA** há **dois** relacionamentos, por isso existem duas chaves estrangeiras para a mesma tabela.
- `CHECK`: a saída tem que ser depois da entrada, e a data de saída e a guarita de saída são preenchidas juntas.
""")
sql("""
CREATE TABLE estadia (
  cod_estadia SERIAL PRIMARY KEY,
  data_hora_entrada TIMESTAMP NOT NULL,
  data_hora_saida TIMESTAMP,
  num_cartao INTEGER NOT NULL REFERENCES cartao_acesso(num_cartao),
  placa CHAR(7) NOT NULL REFERENCES veiculo(placa),
  guarita_entrada INTEGER NOT NULL REFERENCES guarita(cod_guarita),
  guarita_saida INTEGER REFERENCES guarita(cod_guarita),
  CONSTRAINT saida_depois_entrada CHECK (data_hora_saida > data_hora_entrada),
  CONSTRAINT saida_completa CHECK ((data_hora_saida IS NULL) = (guarita_saida IS NULL))
);
""", CRIAR)

md("""
### 2.8 Pagamento (avulso) e mensalidade (mensalista)

- **ESTADIA (1) – GERA – (1) PAGAMENTO:** relacionamento **1:1**. A chave estrangeira `cod_estadia` é `UNIQUE`, então uma estadia tem no máximo um pagamento. É `NOT NULL` porque todo pagamento é de uma estadia (participação total).
- **CLIENTE (1) – PAGA – (N) MENSALIDADE:** um cliente só pode ter uma mensalidade por mês (`UNIQUE (cod_cliente, mes_referencia)`).
- Valores sempre positivos (`CHECK`).
""")
sql("""
CREATE TABLE pagamento (
  cod_pagamento SERIAL PRIMARY KEY,
  valor NUMERIC(8,2) NOT NULL CHECK (valor > 0),
  data_hora_pagamento TIMESTAMP NOT NULL,
  forma_pagamento forma_pagamento NOT NULL,
  cod_estadia INTEGER NOT NULL UNIQUE REFERENCES estadia(cod_estadia)
);

CREATE TABLE mensalidade (
  cod_mensalidade SERIAL PRIMARY KEY,
  mes_referencia DATE NOT NULL,
  valor NUMERIC(8,2) NOT NULL CHECK (valor > 0),
  data_vencimento DATE NOT NULL,
  data_pagamento DATE,
  cod_cliente INTEGER NOT NULL REFERENCES cliente(cod_cliente),
  UNIQUE (cod_cliente, mes_referencia)
);
""", CRIAR)

md("""
### 2.9 Atributo derivado: status da mensalidade

O status **não é guardado**, porque mudaria sozinho com o passar dos dias. Ele é calculado a partir das datas:

- `PAGO`: tem data de pagamento
- `EM ATRASO`: não foi paga e o vencimento já passou
- `PENDENTE`: não foi paga e ainda está no prazo

Para não repetir esse cálculo em toda consulta, criamos uma **view** (uma consulta salva que pode ser usada como se fosse uma tabela).
""")
sql("""
CREATE VIEW vw_mensalidade_status AS
  SELECT m.*,
         CASE
           WHEN m.data_pagamento IS NOT NULL THEN 'PAGO'
           WHEN m.data_vencimento < CURRENT_DATE THEN 'EM ATRASO'
           ELSE 'PENDENTE'
         END AS status
  FROM mensalidade m;
""", CRIAR)
md("Conferindo as tabelas criadas:")
bash('!posql -c "\\d"')
bash('!posql -c "\\d estadia"')

# =====================================================================
md("""
## 3. População do banco

Os dados representam um mês de funcionamento do estacionamento (outubro de 2026) e alguns veículos que estão no pátio agora. Inserimos sempre informando as colunas (`INSERT INTO tabela (colunas) VALUES ...`), assim os campos `SERIAL` são gerados automaticamente.
""")
sql("""
INSERT INTO fabricante (nome_fabricante) VALUES
  ('Fiat'), ('Volkswagen'), ('Toyota'), ('Mercedes-Benz'),
  ('Honda'), ('Chevrolet'), ('Hyundai');

INSERT INTO modelo (nome_modelo, cod_fabricante) VALUES
  ('Argo', 1), ('Mobi', 1), ('Gol', 2), ('Polo', 2),
  ('Corolla', 3), ('Hilux', 3), ('Sprinter', 4), ('CG 160', 5),
  ('Civic', 5), ('Onix', 6), ('S10', 6), ('HB20', 7);

INSERT INTO categoria (descricao, isenta) VALUES
  ('Carro de passeio', FALSE),
  ('Motocicleta', FALSE),
  ('Caminhonete', FALSE),
  ('Ambulância', TRUE),
  ('Veículo médico', TRUE);

INSERT INTO guarita (localizacao) VALUES
  ('Entrada principal - Av. Central'),
  ('Portaria da emergência'),
  ('Acesso dos funcionários - Rua Lateral');
""", POPULAR)
bash('!posql -c "SELECT * FROM modelo"')

md("""
**Clientes (mensalistas).** O telefone é inserido como `ARRAY[...]` (multivalorado) e o endereço como uma tupla `ROW(...)` (composto).
""")
sql("""
INSERT INTO cliente (nome, cpf, telefone, endereco) VALUES
  ('Ana Souza', '12345678901', ARRAY['84999990001', '8432110001'],
   ROW('Rua das Flores', 120, 'Tirol', 'Natal', 'RN', '59020000')),
  ('Carlos Lima', '98765432100', ARRAY['84988880002'],
   ROW('Av. Salgado Filho', 3000, 'Lagoa Nova', 'Natal', 'RN', '59075000')),
  ('Juliana Ramos', '45678912300', ARRAY['84977770003', '84933330003'],
   ROW('Rua Mossoró', 45, 'Petrópolis', 'Natal', 'RN', '59012000')),
  ('Roberto Alves', '32165498700', ARRAY['84966660004'],
   ROW('Rua São José', 800, 'Centro', 'Parnamirim', 'RN', '59140000'));
""", POPULAR)
bash('!posql -c "SELECT * FROM cliente"')

md("""
**Veículos.** Os cinco primeiros são de mensalistas (a Ana tem dois carros). Os demais são avulsos (`cod_cliente` nulo), incluindo duas ambulâncias e um veículo médico.
""")
sql("""
INSERT INTO veiculo (placa, cor, ano, cod_modelo, cod_categoria, cod_cliente) VALUES
  ('QWE1A23', 'Prata', 2022, 1, 1, 1),
  ('ANA2B34', 'Branco', 2018, 2, 1, 1),
  ('MTO3D67', 'Vermelha', 2023, 8, 2, 2),
  ('JUL4C56', 'Cinza', 2021, 5, 1, 3),
  ('ROB5D78', 'Preto', 2020, 11, 3, 4),
  ('RNB2C45', 'Branco', 2019, 3, 1, NULL),
  ('TYT4E89', 'Preto', 2020, 6, 3, NULL),
  ('HBX6F12', 'Azul', 2017, 12, 1, NULL),
  ('ONX7G34', 'Branco', 2024, 10, 1, NULL),
  ('PLO8H56', 'Vermelho', 2022, 4, 1, NULL),
  ('CVC9J78', 'Prata', 2016, 9, 1, NULL),
  ('AMB0A01', 'Branco', 2021, 7, 4, NULL),
  ('AMB0A02', 'Branco', 2023, 7, 4, NULL),
  ('MED1K23', 'Branco', 2022, 6, 5, NULL);
""", POPULAR)

md("""
**Cartões.** O Carlos perdeu o cartão 1002 e recebeu o 1003 (o histórico fica guardado). O cartão do Roberto está bloqueado. Os cartões da série 2000 são avulsos e circulam entre os visitantes.
""")
sql("""
INSERT INTO cartao_acesso (num_cartao, tipo, status, data_emissao, data_validade, cod_cliente) VALUES
  (1001, 'MENSALISTA', 'ATIVO',     '2026-03-01', '2027-03-01', 1),
  (1002, 'MENSALISTA', 'PERDIDO',   '2026-04-01', '2027-04-01', 2),
  (1003, 'MENSALISTA', 'ATIVO',     '2026-08-15', '2027-08-15', 2),
  (1004, 'MENSALISTA', 'ATIVO',     '2026-05-10', '2027-05-10', 3),
  (1005, 'MENSALISTA', 'BLOQUEADO', '2026-02-01', '2027-02-01', 4),
  (2001, 'AVULSO', 'ATIVO', '2026-01-05', NULL, NULL),
  (2002, 'AVULSO', 'ATIVO', '2026-01-05', NULL, NULL),
  (2003, 'AVULSO', 'ATIVO', '2026-01-05', NULL, NULL),
  (2004, 'AVULSO', 'ATIVO', '2026-01-05', NULL, NULL),
  (2005, 'AVULSO', 'ATIVO', '2026-01-05', NULL, NULL),
  (2006, 'AVULSO', 'ATIVO', '2026-01-05', NULL, NULL);
""", POPULAR)
bash('!posql -c "SELECT * FROM cartao_acesso"')

md("""
**Estadias.** As 13 primeiras já terminaram (outubro de 2026). As 3 últimas estão **no pátio agora**: não têm saída, e a entrada é calculada a partir do horário atual (`NOW() - INTERVAL '...'`).
""")
sql("""
INSERT INTO estadia (data_hora_entrada, data_hora_saida, num_cartao, placa, guarita_entrada, guarita_saida) VALUES
  ('2026-10-01 08:00:00', '2026-10-01 10:30:00', 2001, 'RNB2C45', 1, 1),
  ('2026-10-01 07:10:00', '2026-10-01 19:05:00', 1001, 'QWE1A23', 3, 3),
  ('2026-10-02 13:20:00', '2026-10-02 14:05:00', 2002, 'HBX6F12', 1, 2),
  ('2026-10-03 02:15:00', '2026-10-03 02:55:00', 2003, 'AMB0A01', 2, 2),
  ('2026-10-05 09:00:00', '2026-10-05 17:40:00', 1004, 'JUL4C56', 1, 1),
  ('2026-10-06 10:00:00', '2026-10-06 16:20:00', 2001, 'ONX7G34', 1, 1),
  ('2026-10-08 15:30:00', '2026-10-08 16:10:00', 2004, 'MED1K23', 2, 1),
  ('2026-10-10 07:50:00', '2026-10-10 18:00:00', 1003, 'MTO3D67', 3, 3),
  ('2026-10-12 11:00:00', '2026-10-12 13:30:00', 2002, 'PLO8H56', 1, 1),
  ('2026-10-15 20:00:00', '2026-10-16 08:30:00', 2005, 'CVC9J78', 2, 1),
  ('2026-10-18 08:15:00', '2026-10-18 12:00:00', 1001, 'ANA2B34', 1, 1),
  ('2026-10-20 09:40:00', '2026-10-20 10:20:00', 2003, 'RNB2C45', 1, 2),
  ('2026-10-25 06:30:00', '2026-10-25 07:10:00', 2006, 'AMB0A02', 2, 2),
  (NOW() - INTERVAL '3 hours',  NULL, 2001, 'TYT4E89', 1, NULL),
  (NOW() - INTERVAL '2 hours',  NULL, 1004, 'JUL4C56', 3, NULL),
  (NOW() - INTERVAL '50 minutes', NULL, 2002, 'HBX6F12', 1, NULL);
""", POPULAR)

md("""
**Pagamentos dos avulsos.** Regra de cobrança: **R$ 5,00 por hora iniciada**. Estadias de mensalistas (2, 5, 8, 11) e de veículos isentos (4, 7, 13) não geram pagamento.
""")
sql("""
INSERT INTO pagamento (valor, data_hora_pagamento, forma_pagamento, cod_estadia) VALUES
  (15.00, '2026-10-01 10:27:00', 'PIX', 1),
  (5.00,  '2026-10-02 14:01:00', 'DINHEIRO', 3),
  (35.00, '2026-10-06 16:15:00', 'CARTAO', 6),
  (15.00, '2026-10-12 13:25:00', 'PIX', 9),
  (65.00, '2026-10-16 08:22:00', 'CARTAO', 10),
  (5.00,  '2026-10-20 10:16:00', 'PIX', 12);
""", POPULAR)

md("""
**Mensalidades.** Vencimento todo dia 10. A Juliana não pagou outubro, e o Roberto não paga desde setembro (por isso o cartão dele foi bloqueado).
""")
sql("""
INSERT INTO mensalidade (mes_referencia, valor, data_vencimento, data_pagamento, cod_cliente) VALUES
  ('2026-09-01', 250.00, '2026-09-10', '2026-09-08', 1),
  ('2026-10-01', 250.00, '2026-10-10', '2026-10-09', 1),
  ('2026-11-01', 250.00, '2026-11-10', NULL,         1),
  ('2026-09-01', 120.00, '2026-09-10', '2026-09-05', 2),
  ('2026-10-01', 120.00, '2026-10-10', '2026-10-12', 2),
  ('2026-11-01', 120.00, '2026-11-10', NULL,         2),
  ('2026-09-01', 250.00, '2026-09-10', '2026-09-10', 3),
  ('2026-10-01', 250.00, '2026-10-10', NULL,         3),
  ('2026-11-01', 250.00, '2026-11-10', NULL,         3),
  ('2026-09-01', 300.00, '2026-09-10', NULL,         4),
  ('2026-10-01', 300.00, '2026-10-10', NULL,         4);
""", POPULAR)
md("Quantidade de linhas em cada tabela:")
sql("""
SELECT 'fabricante' AS tabela, COUNT(*) FROM fabricante UNION ALL
SELECT 'modelo', COUNT(*) FROM modelo UNION ALL
SELECT 'categoria', COUNT(*) FROM categoria UNION ALL
SELECT 'cliente', COUNT(*) FROM cliente UNION ALL
SELECT 'veiculo', COUNT(*) FROM veiculo UNION ALL
SELECT 'cartao_acesso', COUNT(*) FROM cartao_acesso UNION ALL
SELECT 'guarita', COUNT(*) FROM guarita UNION ALL
SELECT 'estadia', COUNT(*) FROM estadia UNION ALL
SELECT 'pagamento', COUNT(*) FROM pagamento UNION ALL
SELECT 'mensalidade', COUNT(*) FROM mensalidade;
""", POPULAR)

# =====================================================================
md("""
## 4. Testes das restrições

Cada comando abaixo **deve dar erro**. É o banco impedindo dados que não fazem sentido no minimundo.

Observação: mesmo quando o `INSERT` falha, o `SERIAL` já gastou o próximo número. Por isso, se novas linhas forem inseridas depois, os códigos vão "pular" alguns valores.
""")
sql_erro("""
INSERT INTO cartao_acesso (num_cartao, tipo, data_emissao, cod_cliente)
VALUES (2099, 'AVULSO', '2026-11-01', 1);
""", "cartão AVULSO não pode ter cliente (check cartao_tipo_cliente)")
sql_erro("""
INSERT INTO estadia (data_hora_entrada, num_cartao, placa, guarita_entrada)
VALUES ('2026-11-01 10:00:00', 2005, 'XYZ9Z99', 1);
""", "o veículo XYZ9Z99 não está cadastrado (chave estrangeira)")
sql_erro("""
INSERT INTO pagamento (valor, data_hora_pagamento, forma_pagamento, cod_estadia)
VALUES (10.00, '2026-10-01 10:40:00', 'PIX', 1);
""", "a estadia 1 já tem pagamento: relação 1:1 (unique)")
sql_erro("""
UPDATE estadia SET data_hora_saida = '2026-10-01 07:00:00' WHERE cod_estadia = 1;
""", "a saída não pode ser antes da entrada (check saida_depois_entrada)")
sql_erro("""
INSERT INTO veiculo (placa, cor, ano, cod_modelo, cod_categoria)
VALUES ('abc-123', 'Azul', 2020, 1, 1);
""", "placa fora do padrão (check)")
sql_erro("""
INSERT INTO cartao_acesso (num_cartao, tipo, status, data_emissao)
VALUES (2100, 'AVULSO', 'EXTRAVIADO', '2026-11-01');
""", "EXTRAVIADO não é um valor do enum status_cartao")

# =====================================================================
md("""
## 5. Consultas (exemplos de utilização)

Cada consulta traz a pergunta que ela responde e, quando possível, a expressão equivalente em álgebra relacional.

### 5.1 Atributo composto e multivalorado

Clientes de Natal, com bairro (parte do endereço composto) e quantidade de telefones (tamanho do array).

$\\pi_{\\text{nome, bairro, telefones}}(\\sigma_{\\text{cidade='Natal'}}(\\text{cliente}))$
""")
sql("""
SELECT nome,
       (endereco).bairro AS bairro,
       telefone[1] AS telefone_principal,
       ARRAY_LENGTH(telefone, 1) AS qtd_telefones
FROM cliente
WHERE (endereco).cidade = 'Natal';
""", CONSULTAS)

md("""
### 5.2 Quais veículos estão no pátio agora?

Estadias sem saída, juntando veículo, modelo, categoria, cartão e guarita de entrada.

$\\sigma_{\\text{data\\_hora\\_saida IS NULL}}(\\text{estadia} \\bowtie \\text{veiculo} \\bowtie \\text{modelo} \\bowtie \\text{categoria} \\bowtie \\text{cartao\\_acesso} \\bowtie \\text{guarita})$
""")
sql("""
SELECT e.placa, m.nome_modelo, c.descricao AS categoria, ca.tipo AS cartao,
       g.localizacao AS entrou_por,
       DATE_TRUNC('minute', NOW()::TIMESTAMP - e.data_hora_entrada) AS tempo_no_patio
FROM estadia e
  INNER JOIN veiculo v ON e.placa = v.placa
  INNER JOIN modelo m ON v.cod_modelo = m.cod_modelo
  INNER JOIN categoria c ON v.cod_categoria = c.cod_categoria
  INNER JOIN cartao_acesso ca ON e.num_cartao = ca.num_cartao
  INNER JOIN guarita g ON e.guarita_entrada = g.cod_guarita
WHERE e.data_hora_saida IS NULL
ORDER BY e.data_hora_entrada;
""", CONSULTAS)

md("""
### 5.3 Tempo de permanência (atributo derivado) e valor cobrado

O tempo de permanência é calculado (saída menos entrada). O `LEFT JOIN` com pagamento mantém também as estadias que não geraram cobrança (mensalista ou isento), que aparecem com valor vazio.
""")
sql("""
SELECT e.cod_estadia, e.placa, ca.tipo AS cartao, c.isenta,
       e.data_hora_saida - e.data_hora_entrada AS tempo_permanencia,
       p.valor AS valor_pago
FROM estadia e
  INNER JOIN cartao_acesso ca ON e.num_cartao = ca.num_cartao
  INNER JOIN veiculo v ON e.placa = v.placa
  INNER JOIN categoria c ON v.cod_categoria = c.cod_categoria
  LEFT JOIN pagamento p ON p.cod_estadia = e.cod_estadia
WHERE e.data_hora_saida IS NOT NULL
ORDER BY e.cod_estadia;
""", CONSULTAS)

md("""
### 5.4 Situação das mensalidades (atributo derivado)

Usando a view criada na seção 2.9.
""")
sql("""
SELECT c.nome, TO_CHAR(s.mes_referencia, 'MM/YYYY') AS mes, s.valor,
       s.data_vencimento, s.data_pagamento, s.status
FROM vw_mensalidade_status s
  INNER JOIN cliente c ON s.cod_cliente = c.cod_cliente
ORDER BY c.nome, s.mes_referencia;
""", CONSULTAS)

md("""
### 5.5 Quais clientes estão inadimplentes?

$\\pi_{\\text{nome, telefone}}(\\sigma_{\\text{status='EM ATRASO'}}(\\text{vw\\_mensalidade\\_status}) \\bowtie \\text{cliente})$

O `DISTINCT` remove repetições (o Roberto tem dois meses em atraso), como a projeção da álgebra relacional.
""")
sql("""
SELECT DISTINCT c.nome, c.telefone
FROM vw_mensalidade_status s
  INNER JOIN cliente c ON s.cod_cliente = c.cod_cliente
WHERE s.status = 'EM ATRASO';
""", CONSULTAS)

md("""
### 5.6 Histórico de um veículo, com guarita de entrada e de saída (renomeação)

A tabela `guarita` aparece **duas vezes** na mesma consulta (uma para a entrada, outra para a saída). Para diferenciar, renomeamos cada uma com `AS`.

$\\rho_{\\text{ge}}(\\text{guarita})$ e $\\rho_{\\text{gs}}(\\text{guarita})$
""")
sql("""
SELECT e.cod_estadia, e.data_hora_entrada, ge.localizacao AS guarita_entrada,
       e.data_hora_saida, gs.localizacao AS guarita_saida
FROM estadia e
  INNER JOIN guarita AS ge ON e.guarita_entrada = ge.cod_guarita
  LEFT JOIN guarita AS gs ON e.guarita_saida = gs.cod_guarita
WHERE e.placa = 'RNB2C45'
ORDER BY e.data_hora_entrada;
""", CONSULTAS)

md("""
### 5.7 Estadias de veículos isentos (gratuidade)

$\\sigma_{\\text{isenta = true}}(\\text{estadia} \\bowtie \\text{veiculo} \\bowtie \\text{categoria})$
""")
sql("""
SELECT e.cod_estadia, v.placa, c.descricao AS categoria, e.data_hora_entrada, e.data_hora_saida
FROM estadia e
  INNER JOIN veiculo v ON e.placa = v.placa
  INNER JOIN categoria c ON v.cod_categoria = c.cod_categoria
WHERE c.isenta;
""", CONSULTAS)

md("""
### 5.8 União: veículos que passaram pela portaria da emergência

Veículos que **entraram** pela guarita 2 $\\cup$ veículos que **saíram** por ela.
""")
sql("""
SELECT placa FROM estadia WHERE guarita_entrada = 2
UNION
SELECT placa FROM estadia WHERE guarita_saida = 2;
""", CONSULTAS)

md("""
### 5.9 Interseção: mensalistas inadimplentes que estão no pátio agora

Clientes com veículo no pátio $\\cap$ clientes com mensalidade em atraso. Usamos uma tabela temporária, como em aula, para deixar a consulta mais legível.
""")
sql("""
CREATE TEMP TABLE inadimplentes_no_patio AS
  SELECT v.cod_cliente FROM estadia e
    INNER JOIN veiculo v ON e.placa = v.placa
  WHERE e.data_hora_saida IS NULL
  INTERSECT
  SELECT cod_cliente FROM vw_mensalidade_status WHERE status = 'EM ATRASO';

SELECT c.nome, c.telefone
FROM inadimplentes_no_patio i
  INNER JOIN cliente c ON i.cod_cliente = c.cod_cliente;
""", CONSULTAS)

md("""
### 5.10 Subtração: veículos cadastrados que nunca estacionaram

$\\pi_{\\text{placa}}(\\text{veiculo}) - \\pi_{\\text{placa}}(\\text{estadia})$
""")
sql("""
SELECT placa FROM veiculo
EXCEPT
SELECT placa FROM estadia;
""", CONSULTAS)

md("""
### 5.11 Faturamento por mês

Soma dos pagamentos avulsos e das mensalidades pagas, agrupados por mês (`GROUP BY` com as funções de agregação `COUNT` e `SUM`).
""")
sql("""
SELECT TO_CHAR(data_hora_pagamento, 'YYYY-MM') AS mes, 'AVULSO' AS origem,
       COUNT(*) AS quantidade, SUM(valor) AS total
FROM pagamento
GROUP BY TO_CHAR(data_hora_pagamento, 'YYYY-MM')
UNION ALL
SELECT TO_CHAR(data_pagamento, 'YYYY-MM'), 'MENSALIDADE', COUNT(*), SUM(valor)
FROM mensalidade
WHERE data_pagamento IS NOT NULL
GROUP BY TO_CHAR(data_pagamento, 'YYYY-MM')
ORDER BY mes, origem;
""", CONSULTAS)

md("### 5.12 Cartões que não estão ativos")
sql("""
SELECT ca.num_cartao, ca.tipo, ca.status, c.nome AS titular
FROM cartao_acesso ca
  LEFT JOIN cliente c ON ca.cod_cliente = c.cod_cliente
WHERE ca.status <> 'ATIVO';
""", CONSULTAS)

# =====================================================================
# =====================================================================
def celula_md(texto):
    return {"cell_type": "markdown", "metadata": {}, "source": texto.splitlines(keepends=True)}


def celula_codigo(codigo):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [],
            "source": codigo.splitlines(keepends=True)}


def bash_posql(comando, comentario=None):
    # dentro de aspas duplas o bash interpreta ", ` e $nome / ${ / $(
    assert not re.search(r'["`]|\$[\w{(]', comando), f"comando quebraria o posql -c: {comando[:60]}"
    linhas = ["%%bash"]
    if comentario:
        linhas.append(f"# vai dar erro: {comentario}")
    linhas.append(f'posql -c "\n{comando}\n"')
    return "\n".join(linhas)


def gerar():
    celulas = []
    arquivos = {}
    cabecalho = {
        "01_criar_bd.sql": "-- Estacionamento Hospitalar: criação do banco (tipos, tabelas, restrições e view)\n"
                           "-- Executar no banco vazio: psql -d estacionamento -f 01_criar_bd.sql\n",
        "02_popular_bd.sql": "-- Estacionamento Hospitalar: população com dados de exemplo\n",
        "03_consultas.sql": "-- Estacionamento Hospitalar: consultas de exemplo\n",
        "04_testes_restricoes.sql": "-- Estacionamento Hospitalar: comandos que DEVEM falhar (teste das restrições)\n",
    }
    for tipo, conteudo, arquivo in passos:
        if tipo == "md":
            celulas.append(celula_md(conteudo))
        elif tipo == "bash":
            celulas.append(celula_codigo(conteudo))
        elif tipo == "sql":
            celulas.append(celula_codigo(bash_posql(conteudo)))
            arquivos.setdefault(arquivo, [cabecalho[arquivo]]).append(conteudo)
        elif tipo == "sql_erro":
            comando, comentario = conteudo
            celulas.append(celula_codigo(bash_posql(comando, comentario)))
            arquivos.setdefault(arquivo, [cabecalho[arquivo]]).append(f"-- erro esperado: {comentario}\n{comando}")

    notebook = {
        "cells": celulas,
        "metadata": {
            "colab": {"provenance": []},
            "kernelspec": {"display_name": "Python 3", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 0,
    }
    with open(os.path.join(RAIZ, "estacionamento_hospitalar.ipynb"), "w", encoding="utf-8") as f:
        json.dump(notebook, f, ensure_ascii=False, indent=1)

    os.makedirs(os.path.join(RAIZ, "sql"), exist_ok=True)
    for nome, blocos in arquivos.items():
        with open(os.path.join(RAIZ, "sql", nome), "w", encoding="utf-8") as f:
            f.write("\n\n".join(blocos) + "\n")


if __name__ == "__main__":
    gerar()
    print(f"{len(passos)} passos gerados")
