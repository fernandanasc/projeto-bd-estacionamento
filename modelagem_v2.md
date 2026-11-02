# Sistema de Estacionamento Hospitalar – Modelagem (Iteração 2)

## 1. Minimundo (revisado)

O banco de dados apoia a administração do estacionamento de um hospital no controle
de entrada e saída de veículos, dos cartões de acesso e dos pagamentos.

**Dois tipos de uso.** O estacionamento atende dois perfis:

- **Avulso (uso diário):** quem chega para uma consulta ou visita retira um cartão
  na cancela de entrada, estaciona, paga o tempo de permanência na saída e devolve o
  cartão na máquina. O mesmo cartão físico volta para a cancela e é entregue ao
  próximo visitante. A pessoa não é cadastrada; o que fica registrado é o veículo
  (placa) e a estadia.
- **Mensalista:** é o **cliente** do estacionamento (por exemplo, acompanhante de
  paciente internado ou funcionário terceirizado). Ele é cadastrado com nome, CPF,
  telefones e endereço, recebe um cartão pessoal e paga uma **mensalidade**. Na
  cancela, ele só passa o cartão, e a máquina devolve o mesmo cartão para usar em
  outro dia.

**Cartões de acesso.** Cada cartão tem um número único, um tipo (mensalista ou
avulso) e um status (ativo, bloqueado ou perdido). O cartão mensalista pertence a
um cliente e tem data de validade; se ele perder o cartão, o antigo é marcado como
perdido e um novo é emitido, mantendo o histórico. O cartão avulso não pertence a
ninguém.

**Veículos.** Todo veículo que entra é cadastrado pela placa, com cor, ano, modelo
(que pertence a um fabricante) e categoria. Veículos de mensalistas ficam ligados
ao cliente. A **categoria** define a gratuidade: veículos hospitalares e médicos
(ambulância, viatura do hospital) são **isentos**; os demais seguem as regras normais
de cobrança.

**Estadias.** Cada vez que um veículo entra, registra-se uma estadia: data e hora de
entrada, guarita de entrada, cartão usado e veículo. Na saída, registram-se data e
hora de saída e a guarita de saída. O hospital tem várias guaritas, e a entrada e a
saída podem acontecer em guaritas diferentes.

**Pagamentos.**

- Avulso: na saída, a estadia gera **um** pagamento (valor, data e hora, forma de
  pagamento). O valor é calculado pelo tempo de permanência (por exemplo,
  R$ 5,00 por hora iniciada).
- Mensalista: as estadias não geram pagamento; ele paga uma mensalidade por mês,
  com data de vencimento. A mensalidade está **paga** se tem data de pagamento,
  **em atraso** se não tem e o vencimento já passou, e **pendente** nos outros casos.
- Veículo de categoria isenta: a estadia não gera pagamento.

## 2. Entidades e atributos

| Entidade | Atributos (chave sublinhada no DER) | Observação |
|---|---|---|
| CLIENTE | **cod_cliente**, nome, cpf, telefone (multivalorado), endereco (composto: logradouro, numero, bairro, cidade, uf, cep) | Só mensalistas |
| CARTAO_ACESSO | **num_cartao**, tipo, status, data_emissao, data_validade | tipo: MENSALISTA ou AVULSO |
| VEICULO | **placa**, cor, ano | |
| MODELO | **cod_modelo**, nome_modelo | |
| FABRICANTE | **cod_fabricante**, nome_fabricante | |
| CATEGORIA | **cod_categoria**, descricao, isenta | isenta = gratuidade |
| GUARITA | **cod_guarita**, localizacao | |
| ESTADIA | **cod_estadia**, data_hora_entrada, data_hora_saida, tempo_permanencia (derivado) | |
| PAGAMENTO | **cod_pagamento**, valor, data_hora_pagamento, forma_pagamento | Só avulsos |
| MENSALIDADE | **cod_mensalidade**, mes_referencia, valor, data_vencimento, data_pagamento, status (derivado) | Só mensalistas |

## 3. Relacionamentos e cardinalidades

| Relacionamento | Cardinalidade | Participação | Leitura |
|---|---|---|---|
| FABRICANTE – FABRICA – MODELO | 1:N | modelo total, fabricante parcial | Todo modelo tem um fabricante |
| MODELO – INSTANCIA – VEICULO | 1:N | veículo total | Todo veículo é de um modelo |
| CATEGORIA – CLASSIFICA – VEICULO | 1:N | veículo total | Todo veículo tem uma categoria |
| CLIENTE – POSSUI – VEICULO | 1:N | ambos parciais | Só veículos de mensalistas têm dono cadastrado |
| CLIENTE – RECEBE – CARTAO_ACESSO | 1:N | ambos parciais | Cartão avulso não tem dono |
| CARTAO_ACESSO – UTILIZA – ESTADIA | 1:N | estadia total | Toda estadia usa um cartão |
| VEICULO – REALIZA – ESTADIA | 1:N | estadia total | Toda estadia é de um veículo |
| GUARITA – REGISTRA_ENTRADA – ESTADIA | 1:N | estadia total | Toda estadia tem entrada |
| GUARITA – REGISTRA_SAIDA – ESTADIA | 1:N | ambos parciais | Veículo no pátio ainda não saiu |
| ESTADIA – GERA – PAGAMENTO | **1:1** | pagamento total, estadia parcial | Só estadia avulsa e não isenta gera pagamento |
| CLIENTE – PAGA – MENSALIDADE | 1:N | mensalidade total | Toda mensalidade é de um cliente |

## 4. Regras que o DER não mostra (vão virar CHECK ou consultas no SQL)

1. Cartão MENSALISTA precisa ter cliente; cartão AVULSO não pode ter cliente.
2. A data e hora de saída tem que ser posterior à de entrada.
3. Valor de pagamento e de mensalidade tem que ser maior que zero.
4. Um cliente tem no máximo uma mensalidade por mês de referência.

## 5. O que mudou da iteração 1 para a 2

| # | Mudança | Por quê |
|---|---|---|
| 1 | Separação entre **mensalista** e **avulso** (atributo `tipo` no cartão) | Na v1 não ficava claro quem paga como e como o cartão é reutilizado |
| 2 | **CLIENTE** passa a ser só o mensalista; o nome "visitante" deixa de existir | Na v1, texto e diagrama usavam dois nomes para a mesma coisa |
| 3 | O veículo passa a se ligar à **ESTADIA**, não ao cartão | O cartão avulso circula entre vários veículos; quem entrou fica registrado na estadia |
| 4 | Nova relação CLIENTE – POSSUI – VEICULO | Saber quais veículos são do mensalista |
| 5 | PAGAMENTO passa a ser da **ESTADIA** (1:1), não mais de cliente e veículo | O avulso paga a estadia; na v1 não dava para saber qual estadia foi paga |
| 6 | Nova entidade **MENSALIDADE**, com vencimento | A cobrança do mensalista é mensal e precisa de vencimento para o "em atraso" |
| 7 | **STATUS_PAGAMENTO removido**; o status da mensalidade virou atributo **derivado** | Pago, pendente ou em atraso pode ser calculado pelas datas; guardar seria redundante |
| 8 | Status e datas no cartão | Para saber se o cartão vale e manter o histórico de perdas |
| 9 | Atributo `isenta` em CATEGORIA; tarifação diferenciada removida | Simplificação: veículo hospitalar não paga, os demais pagam normal |
| 10 | **VAGA removida** | Difícil de acompanhar no mundo real; não agregava ao objetivo |
| 11 | Telefone **multivalorado** | Um cliente pode ter vários telefones (exemplo do conceito visto em aula) |
| 12 | Fabricante com participação **parcial** em FABRICA | Na v1 era total dos dois lados, o que impedia cadastrar um fabricante antes de seus modelos |
| 13 | Novo atributo derivado `tempo_permanencia` na ESTADIA | É calculado pela diferença entre saída e entrada e usado para cobrar o avulso |

## 6. Do DER para o PostgreSQL (como visto em aula)

| Conceito no DER | No PostgreSQL |
|---|---|
| Atributo chave | `PRIMARY KEY` (chave artificial com `serial`; a placa é chave natural) |
| Atributo composto (endereco) | `CREATE TYPE endereco AS (...)` |
| Atributo multivalorado (telefone) | `text[]` (array) |
| Atributo derivado | Não é guardado; é calculado no `SELECT` |
| Domínio restrito (tipo, status, forma) | `CREATE TYPE ... AS ENUM (...)` |
| Relação 1:N | Chave estrangeira (`REFERENCES`) do lado N |
| Relação 1:1 | Chave estrangeira com `UNIQUE` |
| Participação total | Chave estrangeira `NOT NULL` |
| Participação parcial | Chave estrangeira que aceita `NULL` |
