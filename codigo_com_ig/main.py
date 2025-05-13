# main.py - Com suporte a visualização do mapa em janela separada

from interface import iniciar_interface
from mapa import abrir_mapa_com_webview

if __name__ == "__main__":
    iniciar_interface()
    # Para exibir o mapa, o usuário pode chamar a função abaixo quando desejar:
    # abrir_mapa_com_webview(pedido)  # Substitua 'pedido' por um objeto válido de pedido