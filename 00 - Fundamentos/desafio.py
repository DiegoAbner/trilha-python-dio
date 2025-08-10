# -*- coding: utf-8 -*-
import json
from datetime import datetime
from getpass import getpass
from pathlib import Path

DATA_FILE = Path("contas.json")


def agora_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class Conta:
    def __init__(self, numero, titular, saldo=0.0, limite=500.0,
                 limite_saques=3, senha=None, extrato=None, numero_saques=0):
        self.numero = str(numero)
        self.titular = titular
        self.saldo = float(saldo)
        self.limite = float(limite)
        self.LIMITE_SAQUES = int(limite_saques)
        self.senha = senha or ""
        self.extrato = extrato or []
        self.numero_saques = int(numero_saques)

    def depositar(self, valor):
        if valor <= 0:
            return False, "Operação falhou! O valor informado é inválido."
        self.saldo += valor
        self.extrato.append(f"{agora_str()} - Depósito: R$ {valor:.2f}")
        return True, "Depósito realizado com sucesso."

    def sacar(self, valor):
        if valor <= 0:
            return False, "Operação falhou! O valor informado é inválido."
        if valor > self.saldo:
            return False, "Operação falhou! Você não tem saldo suficiente."
        if valor > self.limite:
            return False, "Operação falhou! O valor do saque excede o limite."
        if self.numero_saques >= self.LIMITE_SAQUES:
            return False, "Operação falhou! Número máximo de saques excedido."
        self.saldo -= valor
        self.numero_saques += 1
        self.extrato.append(f"{agora_str()} - Saque: R$ {valor:.2f}")
        return True, "Saque realizado com sucesso."

    def transferir(self, destino, valor):
        if not isinstance(destino, Conta):
            return False, "Conta destino inválida."
        if valor <= 0:
            return False, "Operação falhou! O valor informado é inválido."
        if valor > self.saldo:
            return False, "Operação falhou! Saldo insuficiente para transferência."
        self.saldo -= valor
        destino.saldo += valor
        self.extrato.append(f"{agora_str()} - Transferência para {destino.numero}: R$ {valor:.2f}")
        destino.extrato.append(f"{agora_str()} - Transferência recebida de {self.numero}: R$ {valor:.2f}")
        return True, "Transferência realizada com sucesso."

    def ver_extrato(self):
        header = "\n================ EXTRATO ================"
        body = "\n".join(self.extrato) if self.extrato else "Não foram realizadas movimentações."
        footer = f"\n\nSaldo: R$ {self.saldo:.2f}\n=========================================="
        return f"{header}\n{body}{footer}"

    def to_dict(self):
        return {
            "numero": self.numero,
            "titular": self.titular,
            "saldo": self.saldo,
            "limite": self.limite,
            "limite_saques": self.LIMITE_SAQUES,
            "senha": self.senha,
            "extrato": self.extrato,
            "numero_saques": self.numero_saques,
        }

    @classmethod
    def from_dict(cls, d):
        return cls(
            numero=d.get("numero"),
            titular=d.get("titular"),
            saldo=d.get("saldo", 0.0),
            limite=d.get("limite", 500.0),
            limite_saques=d.get("limite_saques", 3),
            senha=d.get("senha", ""),
            extrato=d.get("extrato", []),
            numero_saques=d.get("numero_saques", 0),
        )


class Banco:
    def __init__(self):
        self.contas = {}
        self.proxima_conta = 1001

    def criar_conta(self, titular, senha, numero=None, limite=500.0, limite_saques=3):
        if numero is None:
            numero = str(self.proxima_conta)
            self.proxima_conta += 1
        conta = Conta(numero=numero, titular=titular, saldo=0.0,
                      limite=limite, limite_saques=limite_saques, senha=senha)
        self.contas[numero] = conta
        return conta

    def listar_contas(self):
        return list(self.contas.values())

    def obter_conta(self, numero):
        return self.contas.get(str(numero))

    def salvar(self, filepath=DATA_FILE):
        data = {
            "proxima_conta": self.proxima_conta,
            "contas": {num: c.to_dict() for num, c in self.contas.items()}
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def carregar(self, filepath=DATA_FILE):
        if not filepath.exists():
            return
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.proxima_conta = data.get("proxima_conta", self.proxima_conta)
        raw_contas = data.get("contas", {})
        for num, cd in raw_contas.items():
            self.contas[num] = Conta.from_dict(cd)


def leia_float(prompt):
    try:
        v = float(input(prompt).replace(",", "."))
        return v
    except ValueError:
        print("Entrada inválida. Digite um número (use ponto ou vírgula).")
        return None


def menu_principal():
    return """
[d] Depositar
[s] Sacar
[t] Transferir
[c] Criar conta
[l] Listar contas
[a] Selecionar conta
[e] Extrato
[sc] Salvar/Criar backup
[q] Sair

=> """


def main():
    banco = Banco()
    banco.carregar()

    conta_atual = None

    print("Bem-vindo ao Sistema Bancário (versão ampliada)")

    while True:
        opcao = input(menu_principal()).strip().lower()

        if opcao == "c":
            nome = input("Nome do titular: ").strip()
            if not nome:
                print("Nome inválido.")
                continue
            senha = getpass("Defina uma senha para a conta (não será exibida): ").strip()
            if not senha:
                print("Senha inválida. Conta não criada.")
                continue
            conta = banco.criar_conta(titular=nome, senha=senha)
            banco.salvar()
            print(f"Conta criada com sucesso! Número da conta: {conta.numero}")

        elif opcao == "l":
            contas = banco.listar_contas()
            if not contas:
                print("Nenhuma conta cadastrada.")
                continue
            print("\nContas cadastradas:")
            for c in contas:
                print(f"- Nº {c.numero} | Titular: {c.titular} | Saldo: R$ {c.saldo:.2f}")
            print("")

        elif opcao == "a":
            numero = input("Informe o número da conta que deseja acessar: ").strip()
            conta = banco.obter_conta(numero)
            if not conta:
                print("Conta não encontrada. Criando nova conta...")
                nome = input("Nome do titular: ").strip()
                senha = getpass("Defina uma senha para a conta: ").strip()
                conta = banco.criar_conta(titular=nome, senha=senha, numero=numero)
                banco.salvar()
                print(f"Conta {numero} criada com sucesso e selecionada.")
            else:
                senha = getpass("Senha da conta: ").strip()
                if senha != conta.senha:
                    print("Senha incorreta.")
                    continue
            conta_atual = conta

        elif opcao == "d":
            if not conta_atual:
                print("Selecione uma conta primeiro (opção 'a').")
                continue
            v = leia_float("Informe o valor do depósito: R$ ")
            if v is None:
                continue
            ok, msg = conta_atual.depositar(v)
            print(msg)
            if ok:
                banco.salvar()

        elif opcao == "s":
            if not conta_atual:
                print("Selecione uma conta primeiro (opção 'a').")
                continue
            v = leia_float("Informe o valor do saque: R$ ")
            if v is None:
                continue
            ok, msg = conta_atual.sacar(v)
            print(msg)
            if ok:
                banco.salvar()

        elif opcao == "t":
            if not conta_atual:
                print("Selecione uma conta primeiro (opção 'a').")
                continue
            destino_num = input("Número da conta destino: ").strip()
            destino = banco.obter_conta(destino_num)
            if not destino:
                print("Conta destino não encontrada. Criando nova conta...")
                nome_destino = input("Nome do titular da conta destino: ").strip()
                senha_destino = getpass("Defina uma senha para a conta destino: ").strip()
                destino = banco.criar_conta(titular=nome_destino, senha=senha_destino, numero=destino_num)
                banco.salvar()
                print(f"Conta destino {destino_num} criada com sucesso.")
            v = leia_float("Informe o valor da transferência: R$ ")
            if v is None:
                continue
            ok, msg = conta_atual.transferir(destino, v)
            print(msg)
            if ok:
                banco.salvar()

        elif opcao == "e":
            if not conta_atual:
                print("Selecione uma conta primeiro (opção 'a').")
                continue
            print(conta_atual.ver_extrato())

        elif opcao == "sc":
            banco.salvar()
            print(f"Dados salvos em {DATA_FILE.resolve()}")

        elif opcao == "q":
            banco.salvar()
            print("Saindo... Dados salvos. Até mais!")
            break

        else:
            print("Operação inválida, por favor selecione novamente a operação desejada.")


if __name__ == "__main__":
    main()
