# mapa.py - Geração e visualização do mapa com pywebview e folium

import folium
import webview

COORD_PIZZARIA = (-19.816142, -43.961433)


def gerar_mapa_pedido(pedido, nome_arquivo="mapa_pedido.html"):
    mapa = folium.Map(location=COORD_PIZZARIA, zoom_start=13)

    # Ponto da pizzaria
    folium.Marker(
        COORD_PIZZARIA,
        popup="Pizza Piazza (Origem)",
        icon=folium.Icon(color="blue")
    ).add_to(mapa)

    # Círculo de raio de 10km
    folium.Circle(
        location=COORD_PIZZARIA,
        radius=10000,
        color="blue",
        fill=True,
        fill_opacity=0.05
    ).add_to(mapa)

    coord_cliente = pedido.get("coordenadas_cliente")
    if not coord_cliente:
        return

    cor = "green" if pedido["distancia_km"] < 8.5 else "orange" if pedido["distancia_km"] <= 10 else "red"

    folium.Marker(
        location=coord_cliente,
        popup=f"{pedido['cliente']['nome']} ({pedido['distancia_km']} km)",
        icon=folium.Icon(color=cor)
    ).add_to(mapa)

    mapa.save(nome_arquivo)


def abrir_mapa_com_webview(pedido):
    gerar_mapa_pedido(pedido)
    webview.create_window("Mapa da Entrega", "mapa_pedido.html")
    webview.start()
