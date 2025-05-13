# logica.py - VERSÃO OTIMIZADA

import requests
import re
from datetime import datetime, timedelta
import locale
from geopy.distance import geodesic

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

# Variável de taxa de entrega
TAXA_ENTREGA_ATUAL = 5.0  # valor inicial editável durante execução

# Endereço da pizzaria
ENDERECO_PIZZARIA = {
    "rua": "R. Bernardo Ferreira da Cruz, 52",
    "bairro": "Venda Nova",
    "cidade": "Belo Horizonte",
    "uf": "MG",
    "cep": "31610-120",
    "coordenadas": (-19.816142, -43.961433)  # Latitude e longitude da pizzaria
}

# Lista persistente de pedidos
historico_pedidos = []

# Status do pedido
STATUS_PEDIDO = {
    1: "Pedido realizado",
    2: "Fazendo o pedido",
    3: "Pedido pronto",
    4: "Saiu para entrega",
    5: "Entregue",
    6: "Cancelado"
}

# Cores para status
CORES_STATUS = {
    "dentro_do_prazo": "verde",
    "atrasando": "amarelo",
    "atrasado": "laranja",
    "entregue": "azul",
    "cancelado": "vermelho"
}

class Pedido:
    def __init__(self, dados):
        self.id = int(datetime.now().timestamp())
        self.dados = dados
        self.data_criacao = datetime.now()
        self.status_log = [(self.data_criacao, STATUS_PEDIDO[1])]
        self.itens = dados["itens"]
        self.pagamento = dados["pagamento"]
        self.taxa_entrega = TAXA_ENTREGA_ATUAL
        self.coordenadas_cliente = self.obter_coordenadas_cliente(dados)
        self.distancia_km = self.calcular_distancia_entrega()
        self.status_atual = STATUS_PEDIDO[1]
        self.cancelado = False

        if self.distancia_km > 10:
            self.entregavel = False
            self.previsao_entrega = None
            self.mensagem_erro = f"Endereço fora da área de entrega de 10km (distância: {self.distancia_km}km)"
        else:
            self.entregavel = True
            self.previsao_entrega = self.calcular_previsao_entrega()
            self.mensagem_erro = None

        self.total = sum([item['valor'] for item in self.itens]) + self.taxa_entrega

    def obter_coordenadas_cliente(self, dados):
        endereco = f"{dados['logradouro']}, {dados['numero']}, {dados['bairro']}, {dados['cidade']}, {dados['cep']}"
        try:
            response = requests.get(
                f'https://nominatim.openstreetmap.org/search',
                params={'q': endereco, 'format': 'json'},
                headers={'User-Agent': 'Mozilla/5.0'}
            )
            response.raise_for_status()
            data = response.json()
            if not data:
                raise ValueError("Endereço não encontrado")
            return float(data[0]['lat']), float(data[0]['lon'])
        except Exception as e:
            print(f"Erro ao obter coordenadas para {endereco}: {str(e)}")
            return None

    def calcular_distancia_entrega(self):
        if not self.coordenadas_cliente:
            return float('inf')
        return round(geodesic(ENDERECO_PIZZARIA['coordenadas'], self.coordenadas_cliente).km, 2)

    def calcular_previsao_entrega(self):
        tempo_base = len([i for i in self.itens if "PIZZA" in i['descricao']]) * 45  # 45 min per pizza
        tempo_deslocamento = int(self.distancia_km * 2)  # ida e volta
        return self.data_criacao + timedelta(minutes=tempo_base + tempo_deslocamento)

    def atualizar_status(self, novo_status):
        if novo_status in STATUS_PEDIDO.values():
            self.status_atual = novo_status
            self.status_log.append((datetime.now(), novo_status))
            if novo_status == STATUS_PEDIDO[5]:
                self.cor_status = CORES_STATUS['entregue']
        elif novo_status == STATUS_PEDIDO[6]:
            self.cancelado = True
            self.cor_status = CORES_STATUS['cancelado']

    def status_visual(self):
        if self.cancelado:
            return CORES_STATUS['cancelado']
        elif self.status_atual == STATUS_PEDIDO[5]:
            return CORES_STATUS['entregue']
        elif self.previsao_entrega:
            agora = datetime.now()
            if agora < self.previsao_entrega:
                delta = self.previsao_entrega - agora
                if delta.total_seconds() < 10 * 60:
                    return CORES_STATUS['atrasando']
                return CORES_STATUS['dentro_do_prazo']
            else:
                return CORES_STATUS['atrasado']
        return "cinza"

    def gerar_nfe(self):
        cliente = self.dados
        return {
            "numero": self.id,
            "data": self.data_criacao.strftime("%d/%m/%Y %H:%M:%S"),
            "cliente": {
                "nome": cliente["nome"],
                "email": cliente["email"],
                "telefone": cliente["telefone"],
                "endereco": f"{cliente['logradouro']}, {cliente['numero']}, {cliente['bairro']}, {cliente['cidade']}, {cliente['cep']}"
            },
            "itens": self.itens,
            "pagamento": self.pagamento,
            "taxa_entrega": self.taxa_entrega,
            "total": self.total,
            "previsao_entrega": self.previsao_entrega.strftime("%d/%m/%Y %H:%M:%S") if self.previsao_entrega else "Não entregável",
            "distancia_km": self.distancia_km,
            "status": self.status_atual,
            "status_log": [(dt.strftime("%d/%m/%Y %H:%M:%S"), s) for dt, s in self.status_log],
            "cor_status": self.status_visual(),
            "entregavel": self.entregavel
        }


def buscar_cep(cep):
    cep_limpo = re.sub(r'[^0-9]', '', cep)
    if len(cep_limpo) != 8:
        return {"erro": "CEP deve conter 8 dígitos"}

    try:
        response = requests.get(f'https://viacep.com.br/ws/{cep_limpo}/json/')
        response.raise_for_status()
        data = response.json()
        if "erro" in data:
            return {"erro": "CEP não encontrado"}

        return {
            "cep": data["cep"],
            "logradouro": data["logradouro"],
            "bairro": data["bairro"],
            "cidade": data["localidade"],
            "uf": data["uf"],
            "erro": None
        }
    except Exception as e:
        return {"erro": f"Erro ao buscar CEP: {str(e)}"}


def calcular_pedido(dados):
    pedido = Pedido(dados)
    return {
        "preco": pedido.total,
        "resumo": "Resumo do pedido gerado.",
        "valido": pedido.entregavel,
        "nfe": pedido.gerar_nfe(),
        "objeto": pedido,
        "erro": pedido.mensagem_erro if hasattr(pedido, 'mensagem_erro') and pedido.mensagem_erro else None
    }


def setar_taxa_entrega(novo_valor):
    global TAXA_ENTREGA_ATUAL
    TAXA_ENTREGA_ATUAL = novo_valor
    return TAXA_ENTREGA_ATUAL