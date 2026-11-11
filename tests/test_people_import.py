from osnt.people_import import parse_people_csv


def test_osnt_csv():
    people = parse_people_csv(
        "name,company,role,customer\nAda Lovelace,Accenture,Partner,BMI\n"
    )
    assert people[0].name == "Ada Lovelace"
    assert people[0].company == "Accenture"


def test_sales_navigator_headers():
    people = parse_people_csv(
        "First Name,Last Name,Company,Title\nMarie,Curie,Deloitte,Data Scientist\n"
    )
    assert people[0].name == "Marie Curie"
    assert people[0].role == "Data Scientist"
