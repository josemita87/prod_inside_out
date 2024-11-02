from random import choice
#from sec_cik_mapper import StockMapper
import pandas as pd
import random
import json
#mapper = StockMapper()
#cik_exchange_mapper = mapper.cik_to_exchange

#with open('backtesting/drive/datasets/cik_sic_exchange_mapper.json', 'r') as f:

    #cik_sic_exch_map = json.load(f) 



sic_codes = {
    "All Industries": [i for i in range(100, 9900)],
    "Agriculture, Forestry, and Fishing": [i for i in range(100, 900)],
    "Mining": [i for i in range(1000, 1500)],
    "Construction": [i for i in range(1500, 1800)],
    "Manufacturing": [i for i in range(2000, 4000)],
    "Transportation, Communications, Electric, Gas, and Sanitary Services": [i for i in range(4000, 5000)],
    "Wholesale Trade": [i for i in range(5000, 5200)],
    "Retail Trade": [i for i in range(5200, 6000)],
    "Finance, Insurance, and Real Estate": [i for i in range(6000, 6800)],
    "Services": [i for i in range(7000, 9000)],
    "Public Administration": [i for i in range(9100, 9800)],
    "Nonclassifiable Establishments": [9900]

}


all_txs_columns = [
    'id',                       # id INTEGER PRIMARY KEY AUTOINCREMENT
    'link',                     # link TEXT
    'company_cik',              # company_cik INTEGER
    'company_sic',              # company_sic INTEGER
    'ticker',                   # ticker TEXT
    'exchange',                 # exchange TEXT
    'mcap',                     # mcap INTEGER
    'insider_cik',              # insider_cik INTEGER
    'insider_name',             # insider_name TEXT
    'owner_code',               # owner_code TEXT
    'derivative',               # derivative INTEGER
    'rule105b1',                # rule105b1 TEXT
    'acquired_disposed',        # COALESCE(ad, d_ad) AS acquired_disposed
    'tx_shares',                # COALESCE(shares, d_shares) AS tx_shares
    'tx_price',                 # COALESCE(price, d_acquired_price) AS tx_price
    'tx_remaining_shares',      # COALESCE(NULLIF(remaining_shares, 'N/A'), d_remaining_shares) AS tx_remaining_shares
    'tx_ownership',             # COALESCE(direct_indirect_own, d_dir_ind_own) AS tx_ownership
    'tx_direct_holding',        # COALESCE(direct_holding, d_direct_holding) AS tx_direct_holding
    'tx_indirect_holding',      # COALESCE(indirect_holding, d_indirect_holding) AS tx_indirect_holding
    'tx_date',                  # COALESCE(tx_date, d_execution_date) AS tx_date
    'tx_coding',                # COALESCE(coding, d_coding) AS tx_coding
    'tx_value',                 # ROUND(COALESCE(shares * price, d_shares * d_acquired_price)) AS tx_value
]




#LINKS, PATHS, EXPECTED KEYS and HEADERS for filing_spider.py

link_comp_info   = 'https://data.sec.gov/submissions/CIK{cik}.json'
link_filing      = 'https://www.sec.gov/Archives/edgar/data/{cik}/{full_accesion}/{accesion}.txt'

root='nonDerivativeTable/nonDerivativeTransaction'  
derivative_root='derivativeTable/derivativeTransaction'
hold='nonDerivativeTable/nonDerivativeHolding'
derivative_hold='derivativeTable/derivativeHolding'
holding_amounts='postTransactionAmounts/sharesOwnedFollowingTransaction/value'
holding_ownership='ownershipNature/directOrIndirectOwnership/value'

insider_paths = {
        
    'company_cik':        'issuer/issuerCik', 
    'ticker':             'issuer/issuerTradingSymbol',
    'insider_cik':        'reportingOwner/reportingOwnerId/rptOwnerCik',
    'insider_name':       'reportingOwner/reportingOwnerId/rptOwnerName',
    'director':           'reportingOwner/reportingOwnerRelationship/isDirector',
    'officer':            'reportingOwner/reportingOwnerRelationship/isOfficer',
    'ten_percent_owner':  'reportingOwner/reportingOwnerRelationship/isTenPercentOwner',
    'other':              'reportingOwner/reportingOwnerRelationship/isOther',    
    'rule105b1':          'aff10b5One'
    }

paths = {
         
    'shares':             'transactionAmounts/transactionShares/value',
    'acquired_disposed':  'transactionAmounts/transactionAcquiredDisposedCode/value',
    'price':              'transactionAmounts/transactionPricePerShare/value',
    'date':               'transactionDate/value',
    'remaining_shares':   'postTransactionAmounts/sharesOwnedFollowingTransaction/value',
    'ownership':          'ownershipNature/directOrIndirectOwnership/value', 
    'coding':             'transactionCoding/transactionCode',
    'equity_swap':        'transactionCoding/equitySwapInvolved',
    'footnote_id':        'transactionAmounts/transactionShares/footnoteId'
}
    
derivative_paths = {
    
    'd_shares':           'transactionAmounts/transactionShares/value',
    'd_acquired_disposed':               'transactionAmounts/transactionAcquiredDisposedCode/value',
    'd_acquired_price':   'transactionAmounts/transactionPricePerShare/value',
    #'d_strike_price':     'derivativeTable/derivativeTransaction/expirationDate/value',
    'd_execution_date':   'transactionDate/value',
    #'d-exercisable-date': 'exerciseDate/value',
    #'d-expiration-date':  'expirationDate/value',
    'd_remaining_shares': 'postTransactionAmounts/sharesOwnedFollowingTransaction/value',
    'd_ownership':      'ownershipNature/directOrIndirectOwnership/value',
    'd_coding':           'transactionCoding/transactionCode',
    'd_footnote_id':      'transactionAmounts/transactionShares/footnoteId',
    #'d-underlying_shares':'underlyingSecurity/underlyingSecurityShares/value'
}



thirteen_f = {
    
    'issuer_name': './/xmlns:nameOfIssuer',
    'issuer_cusip': './/xmlns:cusip',
    'title_class': './/xmlns:titleOfClass',
    'shares': './/xmlns:sshPrnamt',
#shrsOrPrnAmt?, investmentDiscretion>DFND?
}   



header_list = [
    {
        'User-Agent': 'CompanyA DataAccess admin@companya.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    },
    {
        'User-Agent': 'CompanyB FinancialAnalytics admin@companyb.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    },
    {
        'User-Agent': 'CompanyC MarketResearch admin@companyc.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    },
    {
        'User-Agent': 'CompanyD TradingPlatform admin@companyd.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    },
    {
        'User-Agent': 'CompanyE InvestmentServices admin@companye.com',
        'Accept-Encoding': 'gzip, deflate',
        'Host': 'www.sec.gov'
    }
]
headers = random.choice(header_list)



   
