import pandas as pd
import datetime
from os.path import exists


class Statement:
    """
    baseline statement cls
    """
    def __init__(self, path):
        self.path = path
        if exists(self.path):
            self.df = pd.read_csv(self.path, index_col=0)
        else:
            self.create_new()
            self.df = pd.read_csv(self.path, index_col=0)

    def create_new(self):
        pass

    def entry(self, category, amount):
        self.df.at[category, 'USD'] += amount
        self.update()

    def remove(self, category, amount):
        self.df.at[category, 'USD'] -= amount
        self.update()

    def update(self):
        pass

    def download(self):
        self.df.to_csv(self.path)


class IncStat(Statement):
    """
    Gross Income: rent, late fee
    Gross Expense: pm, repair, maintenance, utilty, legal&pro, insurance, tax
    *Operating Income = [sum]
    Capital Income: invest
    Capital Expense: interest
    *Net Income = [op inc + sum]

    * auto-calculate
    """
    def create_new(self):
        pd.DataFrame({'USD': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00]},
                     index=['Gross Income', 'Gross Expense',
                            'Operating Income',
                            'Capital Income', 'Capital Expense',
                            'Net Income']).to_csv(self.path)

    def update(self):
        self.df.at['Operating Income', 'USD'] = self.df.at['Gross Income', 'USD'] - self.df.at['Gross Expense', 'USD']
        self.df.at['Net Income', 'USD'] = self.df.at['Operating Income', 'USD'] + self.df.at['Capital Income', 'USD'] - self.df.at['Capital Expense', 'USD']


class BalSht(Statement):
    """
    Cash:
    Account Receivable: owed
    Securities: owned shares
    Property: property
    *Total Asset = [ass curr + ass long]
    Account Payable:
    Unearned Revenue: write offs
    Debt:
    *Total Liability = [liab curr + liab long]
    Contributed Capital
    Previous Retained Earning
    *Retained Earning = [Previous Retained Earning + net inc]
    *Total Equity = [Contributed Capital + Retained Earning]

    * auto-calculate

    Balanced: bool
    *Check eq = [cap + retained earning]
    *Check eq = [ass - liab]
    """
    def __init__(self, path):
        super().__init__(path)
        self.balance = self.check_balance()

    def create_new(self):
        pd.DataFrame({'USD': [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]},
                     index=['Cash', 'Account Receivable', 'Securities', 'Property', 'Total Asset',
                            'Account Payable', 'Unearned Revenue', 'Debt', 'Total Liability',
                            'Contributed Capital', 'Previous Retained Earning', 'Retained Earning', 'Total Equity']).to_csv(self.path)

    def check_balance(self):
        if (self.df.at['Total Asset', 'USD'] - self.df.at['Total Liability', 'USD']) == self.df.at['Total Equity', 'USD']:
            return True
        return False

    def update(self):
        self.df.at['Total Asset', 'USD'] = self.df.at['Cash', 'USD'] + self.df.at['Account Receivable', 'USD'] + self.df.at['Securities', 'USD'] + self.df.at['Property', 'USD']
        self.df.at['Total Liability', 'USD'] = self.df.at['Account Payable', 'USD'] + self.df.at['Unearned Revenue', 'USD'] + self.df.at['Debt', 'USD']
        self.df.at['Total Equity', 'USD'] = self.df.at['Contributed Capital', 'USD'] + self.df.at['Retained Earning', 'USD']
        self.balance = self.check_balance()


class Ledger(Statement):
    def create_new(self):
        pd.DataFrame(columns=['Date', 'Property', 'Unit', 'Category', 'Description', 'Cost', 'Bill']).to_csv(self.path)

    def entry(self, transact):
        self.df = self.df.append(transact, ignore_index=True)


class FinStat:
    """
    For PRE
    """
    def __init__(self, ledger_path, inc_path, bal_path):
        self.ledger = Ledger(ledger_path)
        self.inc_stat = IncStat(inc_path)
        self.bal_sht = BalSht(bal_path)

    def update(self):
        self.bal_sht.df.at['Retained Earning', 'USD'] = self.inc_stat.df.at['Net Income', 'USD'] + self.bal_sht.df.at['Previous Retained Earning', 'USD']
        self.bal_sht.update()

    def transaction(self, prop, unit, category, cost, bill, tgt_cat="Cash", date=datetime.datetime.now().date(), description=''):
        """
        :param prop: str - address
        :param cost: float - real cost
        :param bill: str - entity to invoice
        :param category: str - ...
        :param tgt_cat: str - target category in balance sheet
        :param description: str - ...
        :param unit: int
        :param date: datetime - date of transaction
        :rtype: none
        """
        transact = {'Date': date,
                    'Property': prop,
                    'Unit': unit,
                    'Category': category,
                    'Description': description,
                    'Cost': cost,
                    'Bill': bill}
        tmp_ledger = self.ledger.df.copy()
        tmp_inc_stat = self.inc_stat.df.copy()
        tmp_bal_sht = self.bal_sht.df.copy()
        try:
            self.ledger.df = self.ledger.df.append(transact, ignore_index=True)
            if category in self.inc_stat.df.index:
                self.inc_stat.entry(category, cost)
                self.update()
                if "Income" in category:
                    self.bal_sht.entry(tgt_cat, cost)
                elif "Expense" in category:
                    self.bal_sht.entry(tgt_cat, -cost)
            elif category in self.bal_sht.df.index:
                self.bal_sht.entry(category, cost)
            else:
                raise NameError("Unknown category!")
            if not self.bal_sht.balance:
                raise NameError("Unbalanced accounts!")
        except NameError:
            self.revert(tmp_ledger, tmp_inc_stat, tmp_bal_sht, transact)

    def revert(self, rev_ledger, rev_inc, rev_bal, transact):
        print(f"Transaction Error: {transact}")
        self.ledger.df = rev_ledger
        self.inc_stat.df = rev_inc
        self.bal_sht.df = rev_bal

    def export(self):
        self.ledger.download()
        self.inc_stat.download()
        self.bal_sht.download()
