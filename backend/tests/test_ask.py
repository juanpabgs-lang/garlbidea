from garleb_desk.ask.engine import ask

QUESTIONS = [
    "Who is shipping more pasta into Kenya?",
    "Which competitor just entered the Gulf?",
    "Where are prices per tonne heading?",
    "Which freight lane spiked?",
    "What is the US anti-dumping margin on Garofalo?",
    "What should we do about Hormuz?",
    "Trend of Italian pasta into Saudi Arabia",
    "Compare Turkey and Italy in Somalia",
    "Shelf price of spaghetti in Lebanon",
    "What is Foggia durum doing?",
    "EURUSD hedge",
    "Screen this name: Islamic Revolutionary Guard",
    "Jeddah port calls",
    "Jebel Ali vs Khor Fakkan",
    "Ramadan order dates",
    "TMO wheat sales",
    "Garofalo new production lines",
    "Saudi pasta exports",
    "Who leads Qatar pasta imports?",
    "Unit values into Kenya",
    "Tomato paste into the UAE",
    "Semolina prices",
    "News on Puglia farmers",
    "OFAC actions this week",
    "What to do about the 6.47 percent margin",
    "East Africa pasta shares",
    "Gulf route alternatives",
    "Beirut port recovery",
    "Syria shelf vs Lebanon",
    "CCFI Persian Gulf",
    "Suez Canal traffic",
    "Bab el-Mandeb container ships",
    "Italy to Lebanon monthly tonnes",
    "Egypt share in Kenya",
    "Iran in Kenya pasta",
    "What should Massimo tell his father tomorrow?",
    "Landed cost into the UAE",
    "Turkish lira and pasta",
    "FDA pasta recalls",
    "RASFF pasta alerts",
    "Lebanon public food tenders",
    "Who is shipping pasta into Djibouti?",
]


def test_ask_bank_does_not_crash():
    for q in QUESTIONS:
        ans = ask(q)
        assert "text" in ans
        assert ans["question"] == q
        assert ans["intent"]
    assert len(QUESTIONS) >= 40


def test_policy_intent():
    ans = ask("What is the US anti-dumping margin on Garofalo?")
    assert ans["intent"] == "policy"
