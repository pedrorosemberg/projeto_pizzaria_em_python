# interface.py - VERSÃO OTIMIZADA

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog, filedialog
from logica import calcular_pedido, buscar_cep, historico_pedidos, setar_taxa_entrega
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import json

class PizzaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pizza Piazza")
        self.root.geometry("950x700")

        self.sabores = ["Calabresa", "Frango com Catupiry", "Portuguesa", "Três Queijos"]
        self.tamanhos = ["P", "M", "G"]
        self.refrigerantes = ["Nenhum", "Coca-Cola", "Guaraná Antártica", "Fanta Laranja"]
        self.pagamentos = ["Cartão de Crédito", "Cartão de Débito", "Pix", "Dinheiro", "VR", "VA"]

        self.itens_carrinho = []

        # Variáveis do cliente
        self.vars = {
            "nome": tk.StringVar(), "email": tk.StringVar(), "telefone": tk.StringVar(),
            "logradouro": tk.StringVar(), "numero": tk.StringVar(), "bairro": tk.StringVar(),
            "cidade": tk.StringVar(), "uf": tk.StringVar(), "cep": tk.StringVar(),
            "sabor": tk.StringVar(value=self.sabores[0]), "tamanho": tk.StringVar(value="P"),
            "refri": tk.StringVar(value=self.refrigerantes[0]), "pagamento": tk.StringVar(value=self.pagamentos[0])
        }

        self.build_interface()

    def build_interface(self):
        self.frame = ttk.Notebook(self.root)
        self.frame.pack(expand=True, fill='both')

        self.tab_pedido = ttk.Frame(self.frame)
        self.tab_historico = ttk.Frame(self.frame)
        self.frame.add(self.tab_pedido, text="Novo Pedido")
        self.frame.add(self.tab_historico, text="Histórico")

        self.setup_tab_pedido()
        self.setup_tab_historico()

        # Botão para encerrar e gerar PDF
        btn_encerrar = ttk.Button(self.root, text="Encerrar Programa e Gerar PDF de Auditoria", command=self.encerrar)
        btn_encerrar.pack(pady=10)

    def setup_tab_pedido(self):
        top = ttk.Frame(self.tab_pedido)
        top.pack(side="top", fill="x", padx=10, pady=10)

        ttk.Label(top, text="CEP").pack(side="left")
        ttk.Entry(top, textvariable=self.vars["cep"], width=10).pack(side="left", padx=5)
        ttk.Button(top, text="Buscar Endereço", command=self.buscar_endereco).pack(side="left")

        form = ttk.LabelFrame(self.tab_pedido, text="Dados do Cliente")
        form.pack(fill="x", padx=10, pady=5)

        campos = ["nome", "email", "telefone", "logradouro", "numero", "bairro", "cidade", "uf"]
        for i, campo in enumerate(campos):
            ttk.Label(form, text=campo.capitalize()).grid(row=i//2, column=(i%2)*2, padx=5, pady=3, sticky="w")
            ttk.Entry(form, textvariable=self.vars[campo], width=30).grid(row=i//2, column=(i%2)*2+1, padx=5, pady=3)

        pedido_frame = ttk.LabelFrame(self.tab_pedido, text="Montar Pedido")
        pedido_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(pedido_frame, text="Sabor").grid(row=0, column=0, padx=5, pady=5)
        ttk.Combobox(pedido_frame, textvariable=self.vars["sabor"], values=self.sabores, state="readonly").grid(row=0, column=1, padx=5)

        ttk.Label(pedido_frame, text="Tamanho").grid(row=1, column=0, padx=5, pady=5)
        ttk.Combobox(pedido_frame, textvariable=self.vars["tamanho"], values=self.tamanhos, state="readonly").grid(row=1, column=1, padx=5)

        ttk.Label(pedido_frame, text="Refrigerante").grid(row=2, column=0, padx=5, pady=5)
        ttk.Combobox(pedido_frame, textvariable=self.vars["refri"], values=self.refrigerantes, state="readonly").grid(row=2, column=1, padx=5)

        ttk.Button(pedido_frame, text="Adicionar ao Carrinho", command=self.adicionar_ao_carrinho).grid(row=3, column=0, columnspan=2, pady=10)

        self.lista_itens = tk.Listbox(self.tab_pedido, height=6)
        self.lista_itens.pack(fill="x", padx=10)
        ttk.Button(self.tab_pedido, text="Remover Item Selecionado", command=self.remover_item).pack(pady=3)

        pagamento_frame = ttk.LabelFrame(self.tab_pedido, text="Pagamento e Finalização")
        pagamento_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(pagamento_frame, text="Forma de Pagamento").grid(row=0, column=0, padx=5, pady=5)
        ttk.Combobox(pagamento_frame, textvariable=self.vars["pagamento"], values=self.pagamentos, state="readonly").grid(row=0, column=1, padx=5)

        ttk.Button(pagamento_frame, text="Finalizar Pedido", command=self.finalizar_pedido).grid(row=1, column=0, columnspan=2, pady=10)

        ttk.Button(self.tab_pedido, text="Alterar Taxa de Entrega", command=self.alterar_taxa).pack(pady=5)

        self.feedback = tk.Text(self.tab_pedido, height=8, state="disabled", bg="#f7f7f7")
        self.feedback.pack(fill="both", padx=10, pady=10)

    def setup_tab_historico(self):
        self.historico_text = scrolledtext.ScrolledText(self.tab_historico, wrap=tk.WORD)
        self.historico_text.pack(expand=True, fill="both", padx=10, pady=10)

    def buscar_endereco(self):
        cep = self.vars["cep"].get()
        if not cep:
            messagebox.showerror("Erro", "Digite um CEP")
            return

        resultado = buscar_cep(cep)
        if resultado.get("erro"):
            messagebox.showerror("Erro", resultado["erro"])
        else:
            for campo in ["logradouro", "bairro", "cidade", "uf", "cep"]:
                self.vars[campo].set(resultado[campo])

    def adicionar_ao_carrinho(self):
        sabor = self.vars["sabor"].get()
        tamanho = self.vars["tamanho"].get()
        refri = self.vars["refri"].get()
        preco = 10 if tamanho == "P" else 12 if tamanho == "M" else 20
        adicionais = 2 if tamanho == "M" else 10 if tamanho == "G" else 0
        total_item = preco + adicionais
        descricao = f"Pizza {sabor} ({tamanho})"
        self.itens_carrinho.append({"descricao": descricao, "valor": total_item})
        if refri != "Nenhum":
            valor_refri = {"Coca-Cola": 13, "Guaraná Antártica": 10, "Fanta Laranja": 7}[refri]
            self.itens_carrinho.append({"descricao": f"Refrigerante: {refri}", "valor": valor_refri})
        self.atualizar_lista()

    def remover_item(self):
        selec = self.lista_itens.curselection()
        if selec:
            del self.itens_carrinho[selec[0]]
            self.atualizar_lista()

    def atualizar_lista(self):
        self.lista_itens.delete(0, tk.END)
        for item in self.itens_carrinho:
            self.lista_itens.insert(tk.END, f"{item['descricao']} - R$ {item['valor']:.2f}")

    def alterar_taxa(self):
        valor = simpledialog.askfloat("Alterar Taxa", "Digite nova taxa de entrega (R$):", minvalue=0.0)
        if valor is not None:
            nova = setar_taxa_entrega(valor)
            messagebox.showinfo("Taxa Atualizada", f"Nova taxa: R$ {nova:.2f}")

    def finalizar_pedido(self):
        if not self.itens_carrinho:
            messagebox.showerror("Erro", "Adicione itens ao carrinho!")
            return

        dados = {campo: self.vars[campo].get().upper() for campo in self.vars}
        dados["itens"] = self.itens_carrinho.copy()

        resultado = calcular_pedido(dados)
        if not resultado["valido"]:
            messagebox.showwarning("Entrega Não Disponível", "Endereço fora da área de entrega (10km).")
            return

        historico_pedidos.append(resultado["nfe"])
        self.exibir_feedback(resultado["nfe"])
        self.atualizar_historico()
        self.itens_carrinho.clear()
        self.atualizar_lista()
        self.frame.select(self.tab_historico)

    def exibir_feedback(self, pedido):
        self.feedback.config(state="normal")
        self.feedback.delete(1.0, tk.END)
        cor = pedido["cor_status"].upper()
        linhas = [
            f"Pedido #{pedido['numero']} registrado com sucesso.",
            f"Cliente: {pedido['cliente']['nome']}",
            f"Total: R$ {pedido['total']:.2f}",
            f"Previsão de entrega: {pedido['previsao_entrega']}",
            f"Distância: {pedido['distancia_km']} km",
            f"Status: {pedido['status']} ({cor})"
        ]
        self.feedback.insert(tk.END, "\n".join(linhas))
        self.feedback.config(state="disabled")

    def atualizar_historico(self):
        self.historico_text.config(state="normal")
        self.historico_text.delete(1.0, tk.END)
        for pedido in historico_pedidos:
            self.historico_text.insert(tk.END, f"\nPedido #{pedido['numero']} - {pedido['data']}\n")
            for item in pedido['itens']:
                self.historico_text.insert(tk.END, f"  - {item['descricao']} (R$ {item['valor']:.2f})\n")
            self.historico_text.insert(tk.END, f"Total: R$ {pedido['total']:.2f}\n")
            self.historico_text.insert(tk.END, f"Forma de Pagamento: {pedido['pagamento']}\n")
            self.historico_text.insert(tk.END, f"Status: {pedido['status']}\n")
            self.historico_text.insert(tk.END, "-"*40 + "\n")
        self.historico_text.config(state="disabled")

    def encerrar(self):
        nome_pdf = f"auditoria_pedidos_{datetime.now().strftime('%d%m%Y_%H%M')}.pdf"
        path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=nome_pdf)
        if not path:
            return

        doc = SimpleDocTemplate(path, pagesize=letter)
        styles = getSampleStyleSheet()
        content = []

        for pedido in historico_pedidos:
            content.append(Paragraph(f"Pedido #{pedido['numero']}", styles['Title']))
            content.append(Paragraph(f"Data: {pedido['data']}", styles['Normal']))
            content.append(Paragraph(f"Cliente: {pedido['cliente']['nome']}", styles['Normal']))
            content.append(Paragraph(f"Endereço: {pedido['cliente']['endereco']}", styles['Normal']))
            content.append(Paragraph(f"Forma de Pagamento: {pedido['pagamento']}", styles['Normal']))
            content.append(Paragraph(f"Distância: {pedido['distancia_km']} km", styles['Normal']))
            content.append(Paragraph(f"Previsão de Entrega: {pedido['previsao_entrega']}", styles['Normal']))
            content.append(Paragraph(f"Status: {pedido['status']} ({pedido['cor_status']})", styles['Normal']))
            content.append(Spacer(1, 12))

            for item in pedido['itens']:
                content.append(Paragraph(f" - {item['descricao']}: R$ {item['valor']:.2f}", styles['Normal']))

            content.append(Paragraph(f"Taxa de entrega: R$ {pedido['taxa_entrega']:.2f}", styles['Normal']))
            content.append(Paragraph(f"Total: R$ {pedido['total']:.2f}", styles['Normal']))

            content.append(Paragraph("Logs de Status:", styles['Heading3']))
            for log in pedido['status_log']:
                content.append(Paragraph(f" - {log[0]}: {log[1]}", styles['Normal']))

            content.append(PageBreak())

        doc.build(content)
        messagebox.showinfo("Exportado", f"PDF salvo em: {path}")
        self.root.quit()


def iniciar_interface():
    root = tk.Tk()
    app = PizzaApp(root)
    root.mainloop()