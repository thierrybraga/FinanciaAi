# loan_simulation.py

import math
from datetime import date, timedelta


def calculate_amortization(principal_value: float, annual_interest_rate: float,
                           years_value: int, extra_amortization_value: float = 0.0):
    """
    Calcula a tabela de amortização de um empréstimo usando o método da Tabela Price.
    Permite amortização extra que reduz o saldo devedor e recalcula as parcelas futuras.

    Args:
        principal_value (float): O valor principal do empréstimo.
        annual_interest_rate (float): A taxa de juros anual (ex: 1.2 para 1.2%).
        years_value (int): O prazo do empréstimo em anos.
        extra_amortization_value (float): Valor de amortização extra por mês (opcional, padrão 0.0).

    Returns:
        tuple: Uma tupla contendo:
            - list: Uma lista de dicionários, cada um representando uma linha da tabela de amortização.
            - float: Total de juros pagos.
            - float: Total de principal amortizado.
            - float: Total pago (principal + juros).

    Raises:
        ValueError: Se os parâmetros de entrada forem inválidos (ex: valor principal negativo, taxa zero).
        Exception: Para outros erros inesperados durante o cálculo.
    """
    if principal_value <= 0:
        raise ValueError("O valor principal deve ser positivo.")
    if annual_interest_rate < 0:
        raise ValueError("A taxa de juros anual não pode ser negativa.")
    if years_value <= 0:
        raise ValueError("O prazo em anos deve ser positivo.")
    if extra_amortization_value < 0:
        raise ValueError("O valor da amortização extra não pode ser negativo.")

    try:
        monthly_interest_rate = (annual_interest_rate / 100) / 12
        total_months = years_value * 12

        current_balance = principal_value
        schedule = []
        total_interest_paid = 0.0
        total_principal_amortized = 0.0
        total_paid_overall = 0.0

        # Cálculo da parcela mensal fixa (Tabela Price)
        if monthly_interest_rate > 0:
            # Fórmula da Tabela Price
            monthly_payment_fixed = principal_value * (
                        monthly_interest_rate / (1 - math.pow(1 + monthly_interest_rate, -total_months)))
        else:
            # Caso a taxa de juros seja zero
            monthly_payment_fixed = principal_value / total_months if total_months > 0 else 0

        current_month = 1
        while current_balance > 0 and current_month <= total_months:
            interest_for_month = current_balance * monthly_interest_rate

            # Amortização principal da parcela fixa
            principal_payment_fixed = monthly_payment_fixed - interest_for_month

            # Aplicar amortização extra, garantindo que não amortize mais do que o saldo restante
            # e que não seja negativo.
            effective_extra_amortization = min(extra_amortization_value, current_balance - principal_payment_fixed)
            if effective_extra_amortization < 0:
                effective_extra_amortization = 0

            # Total de amortização para o mês (principal da parcela fixa + extra)
            total_amortization_for_month = principal_payment_fixed + effective_extra_amortization

            # Pagamento total do mês
            monthly_payment_actual = interest_for_month + total_amortization_for_month

            # Ajustar para o último mês se o saldo for menor que o pagamento calculado
            if current_balance < total_amortization_for_month:
                total_amortization_for_month = current_balance
                monthly_payment_actual = interest_for_month + total_amortization_for_month
                current_balance = 0
            else:
                current_balance -= total_amortization_for_month

            total_interest_paid += interest_for_month
            total_principal_amortized += total_amortization_for_month
            total_paid_overall += monthly_payment_actual

            schedule.append({
                'month': current_month,
                'payment': monthly_payment_actual,
                'interest': interest_for_month,
                'principal': total_amortization_for_month,
                'balance': max(0.0, current_balance) # Garante que o saldo não seja negativo
            })
            current_month += 1

            # Recalcular parcela fixa para o saldo remanescente se houver amortização extra
            # ou se o saldo foi reduzido significativamente.
            # Isso é crucial para a Tabela Price com amortização extra, a fim de reduzir pagamentos/duração futuros.
            if current_balance > 0 and current_month <= total_months:
                remaining_months = total_months - current_month + 1 # Meses restantes incluindo o atual
                if monthly_interest_rate > 0:
                    # Recalcular pagamento mensal com base no novo saldo e meses restantes
                    monthly_payment_fixed = current_balance * (
                                monthly_interest_rate / (1 - math.pow(1 + monthly_interest_rate, -remaining_months)))
                else:
                    monthly_payment_fixed = current_balance / remaining_months


        return schedule, total_interest_paid, total_principal_amortized, total_paid_overall

    except ValueError as ve:
        raise ve
    except Exception as e:
        # Logar o erro para depuração
        print(f"Erro inesperado no cálculo da amortização: {e}")
        raise Exception(f"Erro inesperado ao calcular a amortização: {e}")
