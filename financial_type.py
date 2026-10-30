import math 

class Assets:
    def __init__(self, name, amount, liquidity, return_rate):
        name = str(name).strip()
        amount = float(amount)
        liquidity = int(liquidity)
        return_rate = float(return_rate)

        if not name:
            raise ValueError('asset name cannot be empty')

        if not math.isfinite(amount) or amount < 0:
            raise ValueError(
                'asset amount must be a finite nonnegative number'
            )

        if liquidity < 1 or liquidity > 5:
            raise ValueError(
                'asset liquidity must be between 1 and 5'
            )

        if (
            not math.isfinite(return_rate)
            or return_rate < -100
            or return_rate > 100
        ):
            raise ValueError(
                'asset return rate must be between -100 and 100'
            )

        self.name = name
        self.amount = amount
        self.liquidity = liquidity
        self.return_rate = return_rate / 100
    
    def __str__(self):
        return (
            f"{self.name}: "
            f"${self.amount:,.2f}, "
            f"{self.liquidity} liquidity, "
            f"{self.return_rate:.2%} return"
        )

    @staticmethod
    def print_table(assets):
        line = "+----------------------+---------------+---------------+-------------+"

        rows = [
            line,
            (
                f"| {'Asset Name':<20} | "
                f"{'Amount':>13} | "
                f"{'Liquidity':^13} | "
                f"{'Return Rate':>11} |"
            ),
            line
        ]

        for asset in assets:
            rows.append(
                f"| {asset.name:<20} | "
                f"${asset.amount:>12,.2f} | "
                f"{asset.liquidity:^13} | "
                f"{asset.return_rate:>11.2%} |"
            )

        rows.append(line)

        return "\n".join(rows)

class Liabilities:
    def __init__(self, name, amount, interest, repayment):
        name = str(name).strip()
        amount = float(amount)
        interest = float(interest)
        repayment = float(repayment)

        if not name:
            raise ValueError('liability name cannot be empty')

        if not math.isfinite(amount) or amount < 0:
            raise ValueError(
                'liability amount must be a finite nonnegative number'
            )

        if (
            not math.isfinite(interest)
            or interest < 0
            or interest > 100
        ):
            raise ValueError(
                'liability interest must be between 0 and 100'
            )

        if not math.isfinite(repayment) or repayment < 0:
            raise ValueError(
                'repayment must be a finite nonnegative number'
            )

        self.name = name
        self.amount = amount
        self.interest = interest / 100
        self.repayment = repayment
        self.term = self.calculate_term()

    def __str__(self):
        if math.isinf(self.term):
            term = "Never"
        else:
            term = f"{math.ceil(self.term)} months"

        return (
            f"{self.name:<20} | "
            f"${self.amount:>12,.2f} | "
            f"{self.interest:>8.2%} | "
            f"${self.repayment:>11,.2f} | "
            f"{term:>12}")
    
    def calculate_term(self):
        if self.amount <= 0:
            return 0

        if self.repayment <= 0:
            return math.inf

        monthly_interest = self.interest / 12

        # no-interest loan
        if monthly_interest == 0:
            return self.amount / self.repayment

        monthly_interest_charge = self.amount * monthly_interest

        # repayment smaller than interest case
        if self.repayment <= monthly_interest_charge:
            return math.inf

        return -math.log(1 - monthly_interest_charge / self.repayment)/ math.log(1 + monthly_interest)

    @staticmethod
    def print_table(liabilities):
        line = (
            "+----------------------+---------------+----------+"
            "--------------+--------------+"
        )

        rows = [
            line,
            (
                f"| {'Liability':<20} | "
                f"{'Amount':>13} | "
                f"{'Interest':>8} | "
                f"{'Repayment':>12} | "
                f"{'Term':>12} |"
            ),
            line
        ]

        for liability in liabilities:
            term = (
                "Never"
                if math.isinf(liability.term)
                else f"{math.ceil(liability.term)} months"
            )

            rows.append(
                f"| {liability.name:<20} | "
                f"${liability.amount:>12,.2f} | "
                f"{liability.interest:>8.2%} | "
                f"${liability.repayment:>11,.2f} | "
                f"{term:>12} |"
            )

        rows.append(line)
        return "\n".join(rows)

class Incomes:
    def __init__(self, name, amount, recurring):
        name = str(name).strip()
        amount = float(amount)

        if not name:
            raise ValueError('income name cannot be empty')

        if not math.isfinite(amount) or amount < 0:
            raise ValueError(
                'income amount must be a finite nonnegative number'
            )

        if not isinstance(recurring, bool):
            raise ValueError('recurring must be True or False')

        self.name = name
        self.amount = amount
        self.recurring = recurring
    
    def recurring_text(self):
        if isinstance(self.recurring, bool):
            return "Yes" if self.recurring else "No"
        return str(self.recurring)

    def __str__(self):
        return (
            f"{self.name}: "
            f"${self.amount:,.2f}, "
            f"recurring: {self.recurring_text()}"
        )

    @staticmethod
    def print_table(incomes):
        line = (
            "+----------------------+---------------+"
            "-----------------+"
        )

        rows = [
            line,
            (
                f"| {'Income Name':<20} | "
                f"{'Amount':>13} | "
                f"{'Recurring':^15} |"
            ),
            line
        ]

        for income in incomes:
            rows.append(
                f"| {income.name:<20} | "
                f"${income.amount:>12,.2f} | "
                f"{income.recurring_text():^15} |"
            )

        rows.append(line)
        return "\n".join(rows)

class Expenses:
    def __init__(self, name, amount, reducible = False, min_amount = 0, rank = 0):
        name = str(name).strip()
        amount = float(amount)
        min_amount = float(min_amount)
        rank = int(rank)

        if not name:
            raise ValueError('expense name cannot be empty')

        if not math.isfinite(amount) or amount < 0:
            raise ValueError(
                'expense amount must be a finite nonnegative number'
            )

        if not isinstance(reducible, bool):
            raise ValueError('reducible must be True or False')

        if not math.isfinite(min_amount) or min_amount < 0:
            raise ValueError(
                'minimum expense must be a finite nonnegative number'
            )

        if min_amount > amount:
            raise ValueError(
                'minimum expense cannot exceed the normal amount'
            )

        if reducible:
            if amount <= 0:
                raise ValueError(
                    'a zero-dollar expense cannot be reducible'
                )

            if min_amount >= amount:
                raise ValueError(
                    'a reducible expense minimum must be below '
                    'the normal amount'
                )

            if rank < 1 or rank > 5:
                raise ValueError(
                    'a reducible expense rank must be between 1 and 5'
                )

        else:
            min_amount = 0.0
            rank = 0

        self.name = name
        self.amount = amount
        self.reducible = reducible
        self.min_amount = min_amount
        self.rank = rank
    
    def reducible_text(self):
        if isinstance(self.reducible, bool):
            return "Yes" if self.reducible else "No"
        return str(self.reducible)

    def __str__(self):
        return (
            f"{self.name}: "
            f"${self.amount:,.2f}, "
            f"reducible: {self.reducible_text()}, "
            f"minimum: ${self.min_amount:,.2f}, "
            f"rank: {self.rank}"
        )
    @staticmethod
    def print_table(expenses):
        line = (
            "+----------------------+---------------+-------------+"
            "---------------+--------+"
        )

        rows = [
            line,
            (
                f"| {'Expense Name':<20} | "
                f"{'Amount':>13} | "
                f"{'Reducible':^11} | "
                f"{'Minimum':>13} | "
                f"{'Rank':^6} |"
            ),
            line
        ]

        for expense in expenses:
            rows.append(
                f"| {expense.name:<20} | "
                f"${expense.amount:>12,.2f} | "
                f"{expense.reducible_text():^11} | "
                f"${expense.min_amount:>12,.2f} | "
                f"{expense.rank:^6} |"
            )

        rows.append(line)
        return "\n".join(rows)
