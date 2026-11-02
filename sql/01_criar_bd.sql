-- Estacionamento Hospitalar: criação do banco (tipos, tabelas, restrições e view)
-- Executar no banco vazio: psql -d estacionamento -f 01_criar_bd.sql


CREATE TYPE endereco AS (
  logradouro TEXT,
  numero INTEGER,
  bairro TEXT,
  cidade TEXT,
  uf CHAR(2),
  cep CHAR(8)
);

CREATE TYPE tipo_cartao AS ENUM ('MENSALISTA', 'AVULSO');
CREATE TYPE status_cartao AS ENUM ('ATIVO', 'BLOQUEADO', 'PERDIDO');
CREATE TYPE forma_pagamento AS ENUM ('DINHEIRO', 'CARTAO', 'PIX');

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

CREATE TABLE cliente (
  cod_cliente SERIAL PRIMARY KEY,
  nome TEXT NOT NULL,
  cpf CHAR(11) NOT NULL UNIQUE CHECK (cpf ~ '^[0-9]{11}$'),
  telefone TEXT[],
  endereco endereco
);

CREATE TABLE veiculo (
  placa CHAR(7) PRIMARY KEY CHECK (placa ~ '^[A-Z]{3}[0-9][A-Z0-9][0-9]{2}$'),
  cor TEXT,
  ano SMALLINT CHECK (ano BETWEEN 1950 AND 2030),
  cod_modelo INTEGER NOT NULL REFERENCES modelo(cod_modelo),
  cod_categoria INTEGER NOT NULL REFERENCES categoria(cod_categoria),
  cod_cliente INTEGER REFERENCES cliente(cod_cliente)
);

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

CREATE TABLE guarita (
  cod_guarita SERIAL PRIMARY KEY,
  localizacao TEXT NOT NULL
);

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

CREATE VIEW vw_mensalidade_status AS
  SELECT m.*,
         CASE
           WHEN m.data_pagamento IS NOT NULL THEN 'PAGO'
           WHEN m.data_vencimento < CURRENT_DATE THEN 'EM ATRASO'
           ELSE 'PENDENTE'
         END AS status
  FROM mensalidade m;
