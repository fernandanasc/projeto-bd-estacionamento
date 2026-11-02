-- Estacionamento Hospitalar: consultas de exemplo


SELECT nome,
       (endereco).bairro AS bairro,
       telefone[1] AS telefone_principal,
       ARRAY_LENGTH(telefone, 1) AS qtd_telefones
FROM cliente
WHERE (endereco).cidade = 'Natal';

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

SELECT c.nome, TO_CHAR(s.mes_referencia, 'MM/YYYY') AS mes, s.valor,
       s.data_vencimento, s.data_pagamento, s.status
FROM vw_mensalidade_status s
  INNER JOIN cliente c ON s.cod_cliente = c.cod_cliente
ORDER BY c.nome, s.mes_referencia;

SELECT DISTINCT c.nome, c.telefone
FROM vw_mensalidade_status s
  INNER JOIN cliente c ON s.cod_cliente = c.cod_cliente
WHERE s.status = 'EM ATRASO';

SELECT e.cod_estadia, e.data_hora_entrada, ge.localizacao AS guarita_entrada,
       e.data_hora_saida, gs.localizacao AS guarita_saida
FROM estadia e
  INNER JOIN guarita AS ge ON e.guarita_entrada = ge.cod_guarita
  LEFT JOIN guarita AS gs ON e.guarita_saida = gs.cod_guarita
WHERE e.placa = 'RNB2C45'
ORDER BY e.data_hora_entrada;

SELECT e.cod_estadia, v.placa, c.descricao AS categoria, e.data_hora_entrada, e.data_hora_saida
FROM estadia e
  INNER JOIN veiculo v ON e.placa = v.placa
  INNER JOIN categoria c ON v.cod_categoria = c.cod_categoria
WHERE c.isenta;

SELECT placa FROM estadia WHERE guarita_entrada = 2
UNION
SELECT placa FROM estadia WHERE guarita_saida = 2;

CREATE TEMP TABLE inadimplentes_no_patio AS
  SELECT v.cod_cliente FROM estadia e
    INNER JOIN veiculo v ON e.placa = v.placa
  WHERE e.data_hora_saida IS NULL
  INTERSECT
  SELECT cod_cliente FROM vw_mensalidade_status WHERE status = 'EM ATRASO';

SELECT c.nome, c.telefone
FROM inadimplentes_no_patio i
  INNER JOIN cliente c ON i.cod_cliente = c.cod_cliente;

SELECT placa FROM veiculo
EXCEPT
SELECT placa FROM estadia;

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

SELECT ca.num_cartao, ca.tipo, ca.status, c.nome AS titular
FROM cartao_acesso ca
  LEFT JOIN cliente c ON ca.cod_cliente = c.cod_cliente
WHERE ca.status <> 'ATIVO';
