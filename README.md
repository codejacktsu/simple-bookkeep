# Simple-BookKeep Quick-Start

### instantiate book
```angular2html
fs = FinStat(ledger_path, inc_path, bal_path)
```

###add transaction
```
fs.transaction(‘WF’, 4, ‘Gross Income’, 100.00, 120.00, ‘BREI’, date=datetime.datetime(2022,1,11).date(), description=‘WF1 Rent’)
```

###display
```
fs.inc_stat.df
```

###is balance sheet balanced?
```
fs.bal_sht.balance
```
###export
```
fs.export()
```
