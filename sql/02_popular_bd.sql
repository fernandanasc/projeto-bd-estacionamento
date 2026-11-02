-- Estacionamento Hospitalar: população com dados de exemplo


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

INSERT INTO cliente (nome, cpf, telefone, endereco) VALUES
  ('Ana Souza', '12345678901', ARRAY['84999990001', '8432110001'],
   ROW('Rua das Flores', 120, 'Tirol', 'Natal', 'RN', '59020000')),
  ('Carlos Lima', '98765432100', ARRAY['84988880002'],
   ROW('Av. Salgado Filho', 3000, 'Lagoa Nova', 'Natal', 'RN', '59075000')),
  ('Juliana Ramos', '45678912300', ARRAY['84977770003', '84933330003'],
   ROW('Rua Mossoró', 45, 'Petrópolis', 'Natal', 'RN', '59012000')),
  ('Roberto Alves', '32165498700', ARRAY['84966660004'],
   ROW('Rua São José', 800, 'Centro', 'Parnamirim', 'RN', '59140000'));

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

INSERT INTO pagamento (valor, data_hora_pagamento, forma_pagamento, cod_estadia) VALUES
  (15.00, '2026-10-01 10:27:00', 'PIX', 1),
  (5.00,  '2026-10-02 14:01:00', 'DINHEIRO', 3),
  (35.00, '2026-10-06 16:15:00', 'CARTAO', 6),
  (15.00, '2026-10-12 13:25:00', 'PIX', 9),
  (65.00, '2026-10-16 08:22:00', 'CARTAO', 10),
  (5.00,  '2026-10-20 10:16:00', 'PIX', 12);

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
