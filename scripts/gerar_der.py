"""Gera o DER (notação de Chen/Elmasri) do estacionamento hospitalar em dois formatos:
- diagramas/der_v2.drawio : editável no draw.io
- diagramas/der_v2.png    : imagem para conferência e slides

Uso: py gerar_der.py
"""
import os
from xml.sax.saxutils import escape
from PIL import Image, ImageDraw, ImageFont

AQUI = os.path.dirname(os.path.abspath(__file__))
SAIDA = os.path.join(AQUI, "..", "diagramas")

DX, DY = 150, 0  # deslocamento global
W_ENT, H_ENT = 180, 56
W_REL, H_REL = 170, 86
H_ATR = 40

# ---------------------------------------------------------------- modelo
# entidades: nome -> (x, y)
entidades = {
    "GUARITA": (1500, 170),
    "CARTAO_ACESSO": (800, 560),
    "ESTADIA": (1500, 560),
    "PAGAMENTO": (2150, 560),
    "CLIENTE": (450, 900),
    "VEICULO": (1500, 1060),
    "MODELO": (2050, 1060),
    "FABRICANTE": (2050, 1420),
    "CATEGORIA": (1500, 1420),
    "MENSALIDADE": (450, 1380),
}

# relacionamentos: nome, (x, y), (entidade A, card A, total A), (entidade B, card B, total B)
relacionamentos = [
    ("REGISTRA_ENTRADA", (1280, 370), ("GUARITA", "1", False), ("ESTADIA", "N", True)),
    ("REGISTRA_SAIDA", (1720, 370), ("GUARITA", "1", False), ("ESTADIA", "N", False)),
    ("UTILIZA", (1150, 560), ("CARTAO_ACESSO", "1", False), ("ESTADIA", "N", True)),
    ("GERA", (1830, 560), ("ESTADIA", "1", False), ("PAGAMENTO", "1", True)),
    ("RECEBE", (620, 730), ("CLIENTE", "1", False), ("CARTAO_ACESSO", "N", False)),
    ("POSSUI", (980, 980), ("CLIENTE", "1", False), ("VEICULO", "N", False)),
    ("REALIZA", (1500, 810), ("VEICULO", "1", False), ("ESTADIA", "N", True)),
    ("INSTANCIA", (1780, 1060), ("MODELO", "1", False), ("VEICULO", "N", True)),
    ("CLASSIFICA", (1500, 1240), ("CATEGORIA", "1", False), ("VEICULO", "N", True)),
    ("FABRICA", (2050, 1240), ("FABRICANTE", "1", False), ("MODELO", "N", True)),
    ("PAGA", (450, 1140), ("CLIENTE", "1", False), ("MENSALIDADE", "N", True)),
]

# atributos: (dono, nome, (x, y), tipo)  tipo: chave | simples | multi | derivado
atributos = [
    ("GUARITA", "cod_guarita", (1330, 90), "chave"),
    ("GUARITA", "localizacao", (1670, 90), "simples"),

    ("CARTAO_ACESSO", "num_cartao", (590, 470), "chave"),
    ("CARTAO_ACESSO", "tipo", (720, 440), "simples"),
    ("CARTAO_ACESSO", "status", (880, 440), "simples"),
    ("CARTAO_ACESSO", "data_emissao", (1010, 470), "simples"),
    ("CARTAO_ACESSO", "data_validade", (940, 650), "simples"),

    ("ESTADIA", "cod_estadia", (1500, 440), "chave"),
    ("ESTADIA", "data_hora_entrada", (1300, 650), "simples"),
    ("ESTADIA", "data_hora_saida", (1320, 715), "simples"),
    ("ESTADIA", "tempo_permanencia", (1700, 660), "derivado"),

    ("PAGAMENTO", "cod_pagamento", (2040, 450), "chave"),
    ("PAGAMENTO", "valor", (2260, 450), "simples"),
    ("PAGAMENTO", "data_hora_pagamento", (2050, 670), "simples"),
    ("PAGAMENTO", "forma_pagamento", (2270, 660), "simples"),

    ("CLIENTE", "cod_cliente", (290, 810), "chave"),
    ("CLIENTE", "nome", (430, 775), "simples"),
    ("CLIENTE", "cpf", (230, 880), "simples"),
    ("CLIENTE", "telefone", (250, 950), "multi"),
    ("CLIENTE", "endereco", (330, 1050), "simples"),

    ("VEICULO", "placa", (1310, 1130), "chave"),
    ("VEICULO", "ano", (1340, 1195), "simples"),
    ("VEICULO", "cor", (1680, 1150), "simples"),

    ("MODELO", "cod_modelo", (1970, 960), "chave"),
    ("MODELO", "nome_modelo", (2150, 960), "simples"),

    ("FABRICANTE", "cod_fabricante", (1960, 1520), "chave"),
    ("FABRICANTE", "nome_fabricante", (2150, 1520), "simples"),

    ("CATEGORIA", "cod_categoria", (1330, 1510), "chave"),
    ("CATEGORIA", "descricao", (1500, 1545), "simples"),
    ("CATEGORIA", "isenta", (1660, 1510), "simples"),

    ("MENSALIDADE", "cod_mensalidade", (250, 1460), "chave"),
    ("MENSALIDADE", "mes_referencia", (330, 1540), "simples"),
    ("MENSALIDADE", "valor", (500, 1555), "simples"),
    ("MENSALIDADE", "data_vencimento", (660, 1510), "simples"),
    ("MENSALIDADE", "data_pagamento", (700, 1430), "simples"),
    ("MENSALIDADE", "status", (680, 1340), "derivado"),
]

# componentes do atributo composto endereco
compostos = [
    ("endereco", "logradouro", (120, 990)),
    ("endereco", "numero", (90, 1050)),
    ("endereco", "bairro", (100, 1110)),
    ("endereco", "cidade", (150, 1170)),
    ("endereco", "uf", (245, 1205)),
    ("endereco", "cep", (330, 1230)),
]


def p(xy):
    return (xy[0] + DX, xy[1] + DY)


def largura_atr(nome):
    return max(90, int(len(nome) * 8.2) + 34)


# ---------------------------------------------------------------- PNG
FONTE = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 15)
FONTE_B = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 16)
FONTE_C = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 17)
CINZA = (232, 232, 232)
PRETO = (20, 20, 20)


def texto_centro(d, xy, txt, fonte, sublinhado=False):
    linhas = txt.split("\n")
    alt = fonte.size + 3
    y0 = xy[1] - alt * len(linhas) / 2
    for i, ln in enumerate(linhas):
        w = d.textlength(ln, font=fonte)
        x = xy[0] - w / 2
        y = y0 + i * alt
        d.text((x, y), ln, fill=PRETO, font=fonte)
        if sublinhado:
            d.line((x, y + fonte.size + 2, x + w, y + fonte.size + 2), fill=PRETO, width=1)


def borda_ret(c, w, h, alvo):
    """ponto em que a reta centro->alvo sai do retângulo"""
    vx, vy = alvo[0] - c[0], alvo[1] - c[1]
    t = min(abs((w / 2) / vx) if vx else 1e9, abs((h / 2) / vy) if vy else 1e9)
    return (c[0] + vx * t, c[1] + vy * t)


def linha(d, a, b, dupla=False):
    if not dupla:
        d.line((a, b), fill=PRETO, width=2)
        return
    vx, vy = b[0] - a[0], b[1] - a[1]
    n = (vx * vx + vy * vy) ** 0.5
    ox, oy = -vy / n * 3, vx / n * 3
    d.line(((a[0] + ox, a[1] + oy), (b[0] + ox, b[1] + oy)), fill=PRETO, width=2)
    d.line(((a[0] - ox, a[1] - oy), (b[0] - ox, b[1] - oy)), fill=PRETO, width=2)


def elipse_tracejada(d, box):
    for ang in range(0, 360, 20):
        d.arc(box, ang, ang + 11, fill=PRETO, width=2)


def gerar_png():
    img = Image.new("RGB", (2560, 1640), "white")
    d = ImageDraw.Draw(img)

    # linhas primeiro (as formas cobrem as pontas)
    for dono, nome, xy, _ in atributos:
        linha(d, p(entidades[dono]), p(xy))
    for pai, nome, xy in compostos:
        linha(d, p(dict((a[1], a[2]) for a in atributos)[pai]), p(xy))
    for nome, xy, a, b in relacionamentos:
        for ent, card, total in (a, b):
            linha(d, p(xy), p(entidades[ent]), dupla=total)

    # atributos
    def desenha_atr(nome, xy, tipo):
        w = largura_atr(nome)
        box = (xy[0] - w / 2, xy[1] - H_ATR / 2, xy[0] + w / 2, xy[1] + H_ATR / 2)
        d.ellipse(box, fill="white")
        if tipo == "derivado":
            elipse_tracejada(d, box)
        else:
            d.ellipse(box, outline=PRETO, width=2)
        if tipo == "multi":
            d.ellipse((box[0] + 5, box[1] + 5, box[2] - 5, box[3] - 5), outline=PRETO, width=2)
        texto_centro(d, xy, nome, FONTE, sublinhado=(tipo == "chave"))

    for dono, nome, xy, tipo in atributos:
        desenha_atr(nome, p(xy), tipo)
    for _, nome, xy in compostos:
        desenha_atr(nome, p(xy), "simples")

    # relacionamentos
    for nome, xy, a, b in relacionamentos:
        x, y = p(xy)
        d.polygon([(x, y - H_REL / 2), (x + W_REL / 2, y), (x, y + H_REL / 2), (x - W_REL / 2, y)],
                  fill=CINZA, outline=PRETO, width=2)
        texto_centro(d, (x, y), nome.replace("_", "_\n") if len(nome) > 10 else nome, FONTE)

    # entidades
    for nome, xy in entidades.items():
        x, y = p(xy)
        d.rectangle((x - W_ENT / 2, y - H_ENT / 2, x + W_ENT / 2, y + H_ENT / 2),
                    fill=CINZA, outline=PRETO, width=2)
        texto_centro(d, (x, y), nome, FONTE_B)

    # cardinalidades, perto da entidade
    for nome, xy, a, b in relacionamentos:
        r = p(xy)
        for ent, card, _ in (a, b):
            e = p(entidades[ent])
            bx, by = borda_ret(e, W_ENT, H_ENT, r)
            vx, vy = r[0] - bx, r[1] - by
            n = (vx * vx + vy * vy) ** 0.5
            ux, uy = vx / n, vy / n
            cx, cy = bx + ux * 32 - uy * 14, by + uy * 32 + ux * 14
            texto_centro(d, (cx, cy), card, FONTE_C)

    # legenda
    d.text((DX + 1780, 160), "Linha dupla = participação total   |   Linha simples = participação parcial", fill=PRETO, font=FONTE)
    d.text((DX + 1780, 185), "Elipse dupla = multivalorado   |   Tracejada = derivado   |   Sublinhado = chave", fill=PRETO, font=FONTE)
    img.save(os.path.join(SAIDA, "der_v2.png"))


# ---------------------------------------------------------------- draw.io
def gerar_drawio():
    cels = []
    ids = {}
    seq = [1]

    def novo_id():
        seq[0] += 1
        return f"c{seq[0]}"

    def vertice(valor, estilo, xy, w, h):
        i = novo_id()
        cels.append(
            f'<mxCell id="{i}" value="{escape(valor)}" style="{estilo}" vertex="1" parent="1">'
            f'<mxGeometry x="{xy[0] - w / 2:.0f}" y="{xy[1] - h / 2:.0f}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return i

    def aresta(origem, destino, dupla=False, rotulo=""):
        i = novo_id()
        estilo = "endArrow=none;html=1;fontStyle=1;fontSize=15;"
        if dupla:
            estilo = "shape=link;" + estilo
        geo = '<mxGeometry relative="1" as="geometry">'
        if rotulo:
            geo = '<mxGeometry x="0.7" y="-12" relative="1" as="geometry"><mxPoint as="offset"/>'
        cels.append(
            f'<mxCell id="{i}" value="{rotulo}" style="{estilo}" edge="1" parent="1" source="{origem}" target="{destino}">'
            f'{geo}</mxGeometry></mxCell>')

    est_ent = "rounded=0;whiteSpace=wrap;html=1;fillColor=#E8E8E8;fontStyle=1;fontSize=14;"
    est_rel = "rhombus;whiteSpace=wrap;html=1;fillColor=#E8E8E8;fontSize=12;"
    est_atr = {
        "simples": "ellipse;whiteSpace=wrap;html=1;fontSize=12;",
        "chave": "ellipse;whiteSpace=wrap;html=1;fontSize=12;fontStyle=4;",
        "multi": "shape=doubleEllipse;whiteSpace=wrap;html=1;fontSize=12;",
        "derivado": "ellipse;whiteSpace=wrap;html=1;fontSize=12;dashed=1;",
    }

    for nome, xy in entidades.items():
        ids[nome] = vertice(nome, est_ent, p(xy), W_ENT, H_ENT)
    atr_ids = {}
    for dono, nome, xy, tipo in atributos:
        i = vertice(nome, est_atr[tipo], p(xy), largura_atr(nome), H_ATR)
        atr_ids[nome] = i
        aresta(ids[dono], i)
    for pai, nome, xy in compostos:
        i = vertice(nome, est_atr["simples"], p(xy), largura_atr(nome), H_ATR)
        aresta(atr_ids[pai], i)
    for nome, xy, a, b in relacionamentos:
        r = vertice(nome.replace("_", "_<br>") if len(nome) > 10 else nome, est_rel, p(xy), W_REL, H_REL)
        for ent, card, total in (a, b):
            aresta(r, ids[ent], dupla=total, rotulo=card)

    xml = (
        '<mxfile host="app.diagrams.net"><diagram name="DER v2" id="der-v2">'
        '<mxGraphModel dx="1600" dy="900" grid="1" gridSize="10" guides="1" page="1" pageScale="1" '
        'pageWidth="2600" pageHeight="1700" math="0" shadow="0"><root>'
        '<mxCell id="0"/><mxCell id="1" parent="0"/>' + "".join(cels) +
        "</root></mxGraphModel></diagram></mxfile>")
    with open(os.path.join(SAIDA, "der_v2.drawio"), "w", encoding="utf-8") as f:
        f.write(xml)


if __name__ == "__main__":
    os.makedirs(SAIDA, exist_ok=True)
    gerar_png()
    gerar_drawio()
    print("ok")
