-- Estacionamento Hospitalar: comandos que DEVEM falhar (teste das restrições)


-- erro esperado: cartão AVULSO não pode ter cliente (check cartao_tipo_cliente)
INSERT INTO cartao_acesso (num_cartao, tipo, data_emissao, cod_cliente)
VALUES (2099, 'AVULSO', '2026-11-01', 1);

-- erro esperado: o veículo XYZ9Z99 não está cadastrado (chave estrangeira)
INSERT INTO estadia (data_hora_entrada, num_cartao, placa, guarita_entrada)
VALUES ('2026-11-01 10:00:00', 2005, 'XYZ9Z99', 1);

-- erro esperado: a estadia 1 já tem pagamento: relação 1:1 (unique)
INSERT INTO pagamento (valor, data_hora_pagamento, forma_pagamento, cod_estadia)
VALUES (10.00, '2026-10-01 10:40:00', 'PIX', 1);

-- erro esperado: a saída não pode ser antes da entrada (check saida_depois_entrada)
UPDATE estadia SET data_hora_saida = '2026-10-01 07:00:00' WHERE cod_estadia = 1;

-- erro esperado: placa fora do padrão (check)
INSERT INTO veiculo (placa, cor, ano, cod_modelo, cod_categoria)
VALUES ('abc-123', 'Azul', 2020, 1, 1);

-- erro esperado: EXTRAVIADO não é um valor do enum status_cartao
INSERT INTO cartao_acesso (num_cartao, tipo, status, data_emissao)
VALUES (2100, 'AVULSO', 'EXTRAVIADO', '2026-11-01');
