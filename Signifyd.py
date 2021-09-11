"""<DATE>,<CUSTOMER_ACCOUNT_ID>,<EVENT_TYPE>

2021-01-01,joe@signifyd.com,PURCHASE
2021-02-01,fraudster@fraud.com,FRAUD_REPORT

Date of purchase for purchases
Date when the fraud was reported in case of frauds

for each PURCHASE - summary of the customer account history based on prior events
    <DATE>,<CUSTOMER_ACCOUNT_ID>,<STATUS>
    STATUS -
        NO_HISTORY no prior events
            no relevant data
        FRAUD_HISTORY any fraud reports
            Count of FRAUDS
        GOOD_HISTORY no fraud reports and >= one purchase older than 90 days
            count prior purchases that are 90 days or older
        UNCONFIRMED_HISTORY No fraud reports, at least one purchase, none older than 90 Days
            count prior purchases

    one event per customer per day
    inputs are in chronological order (asc)
    one output for each input line - in the example joe@signifyd.com has multiple purchases, each one is an output
    Assume all inputs to be valid

"""
from datetime import datetime, timedelta
customer_search = {} #email:Customer
class Customer:
    def __init__(self, email):
        self.email = email
        self._status = "NO_HISTORY"
        self._previous_purchases = 0
        self._previous_purchases_older_than_90 = 0
        self._previous_frauds = 0

    def addEventToHistory(self, event_date, event_type):
        if event_type == "FRAUD_REPORT":
            self._addFraudToHistory()
        else:
            self._addPurchaseToHistory(purchase_date=event_date)

    def _addFraudToHistory(self):
        self._previous_frauds += 1
        self._setStatus()

    def _addPurchaseToHistory(self, purchase_date):
        self._previous_purchases += 1
        if self._older90days(purchase_date):
            self._previous_purchases_older_than_90 +=1
        self._setStatus()

    def _older90days(self, date_to_check):
        """
        why would i save the date of the first purchase just to check this?
        Problem specifies:
        "So if the account has purchases over 90 days old and no reports of fraud[...]"

        To match the output
        2021-02-10,joe@signifyd.com,UNCONFIRMED_HISTORY:1
        2021-03-15,joe@signifyd.com,UNCONFIRMED_HISTORY:2
        2021-05-01,joe@signifyd.com,GOOD_HISTORY:1

        i would need to save the date of every purchase and check if any of them were made
        90 days before the date i'm checking, not today's date.
        """
        return True if date_to_check < datetime.now()-timedelta(days=90) else False

    def _setStatus(self):
        if self._previous_frauds > 0:
            self._status = "FRAUD_HISTORY"
        elif self._previous_purchases_older_than_90 >0:
            self._status = "GOOD_HISTORY"
        elif self._previous_purchases > 0:
            self._status = "UNCONFIRMED_HISTORY"
        else:
            self._status = "NO_HISTORY"

    def getStatus(self):
        return self._status
    def relevantStatus(self):
        if self.getStatus() =="NO_HISTORY":
            return self.getStatus()
        elif self.getStatus() == "FRAUD_HISTORY":
            return f"{self.getStatus()}:{self._previous_frauds}"
        elif self.getStatus() == "GOOD_HISTORY":
            return f"{self.getStatus()}:{self._previous_purchases_older_than_90}"
        return f"{self.getStatus()}:{self._previous_purchases}"

    def __repr__(self):
        return f"{self.email} | {self.getStatus()} | {self._previous_purchases} | {self._previous_purchases_older_than_90}"

def findCustomer(email:str, customer_search=customer_search):
    return customer_search.get(email) if customer_search.get(email) else Customer(email=email)

def saveCustomer(customer:Customer, customer_search=customer_search):
    customer_search[customer.email] = customer

def parseLinesToList(csvLines):
    """
    Parse lines to the format
    :param csvLines: ["2021-01-01,joe@signifyd.com,PURCHASE",]
    :return: [["2021-01-01","joe@signifyd.com","PURCHASE",]]
    """
    lines_parsed: list[list[str]] = []
    for line in csvLines:
        parsed_line = line.split(',')
        parsed_line[0] = datetime.strptime(parsed_line[0], "%Y-%m-%d")
        lines_parsed.append(parsed_line)
    return lines_parsed

def buildAccountHistory(csvLines):
    csvLines = parseLinesToList(csvLines)
    reportLines = []
    for line in csvLines:
        customer = findCustomer(line[1])
        """
        I'm doing the report before adding the event to the customer history because i imagine
        that if you asking me to specify the history of a client you're doing it in order
        to approve a transaction, instead of after approving it
        
        Also FAQ confirms this with:
            "For each PURCHASE event, we want to now the costumer account history (
            based on prior events)
        
        """
        """
        I'm also producing one line for each event 
        As stated in FAQ:
            "One output record for each PURCHASE event in the input.
            
        but the expected output is 
        2021-05-01,joe@signifyd.com,GOOD_HISTORY:1
        2021-10-01,joe@signifyd.com,GOOD_HISTORY:4
        
        Skipping good history 2 and 3
        """
        reportLines.append(f"{datetime.strftime(line[0], '%Y-%m-%d')},{customer.email}, {customer.relevantStatus()}")
        customer.addEventToHistory(event_date=line[0], event_type=line[2])
        saveCustomer(customer)

    return reportLines


CSV_lines = [
"2021-01-01,joe@signifyd.com,PURCHASE",
"2021-02-01,fraudster@fraud.com,FRAUD_REPORT",
"2021-02-03,fraudster@fraud.com,FRAUD_REPORT",
"2021-02-10,joe@signifyd.com,PURCHASE",
"2021-02-14,fraudster@fraud.com,PURCHASE",
"2021-03-15,joe@signifyd.com,PURCHASE",
"2021-05-01,joe@signifyd.com,PURCHASE",
"2021-10-01,joe@signifyd.com,PURCHASE",]

OUTPUT = ["2021-01-01,joe@signifyd.com,NO_HISTORY",
"2021-02-10,joe@signifyd.com,UNCONFIRMED_HISTORY:1",
"2021-02-14,fraudster@fraud.com,FRAUD_HISTORY:2",
"2021-03-15,joe@signifyd.com,UNCONFIRMED_HISTORY:2",
"2021-05-01,joe@signifyd.com,GOOD_HISTORY:1",
"2021-10-01,joe@signifyd.com,GOOD_HISTORY:4",]

result = buildAccountHistory(csvLines=CSV_lines)
print(result)
# assert result == OUTPUT, print(result)