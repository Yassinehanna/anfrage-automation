"""
Beruf definitions -- unchanged from ANFRAGE.py, just moved into its own
module. This stays a fixed, you-maintained dict per the product decision
(not user-editable).
"""

CATEGORIES = {
    "1": {
        "label": "Pflege",
        "berufe": {
            "1": {
                "beruf":   "Pflegefachmann-frau",
                "group":   "pflegefachmann",
                "subject": "Anfrage zur Ausbildung als Pflegefachmann/-frau",
                "tags":    ["amenity=hospital", "amenity=nursing_home",
                            "social_facility=nursing_home", "social_facility=assisted_living"],
                "coverage": "good",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Pflegefachmann in Ihrer Einrichtung, da mir der Umgang mit Menschen sehr am Herzen liegt. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
        },
    },
    "2": {
        "label": "Technik",
        "berufe": {
            "1": {
                "beruf":   "Berufskraftfahrer",
                "group":   "berufskraftfahrer",
                "subject": "Anfrage zur Ausbildung als Berufskraftfahrer",
                "tags":    ["office=logistics"],
                "coverage": "weak",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Berufskraftfahrer in Ihrem Unternehmen, da mich eigenverantwortliches Arbeiten in Transport und Logistik reizt. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
            "2": {
                "beruf":   "Elektroniker",
                "group":   "elektro",
                "subject": "Anfrage zur Ausbildung als Elektroniker",
                "tags":    ["craft=electrician", "shop=electrical"],
                "coverage": "good",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Elektroniker in Ihrem Betrieb, da mir technische Zusammenhänge und praktisches Arbeiten viel Freude bereiten. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
            "3": {
                "beruf":   "Industrieelektriker",
                "group":   "elektro",
                "subject": "Anfrage zur Ausbildung als Industrieelektriker",
                "tags":    ["craft=electrician"],
                "coverage": "weak",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Industrieelektriker in Ihrem Unternehmen, da mich die Arbeit an industriellen Anlagen und elektrischen Systemen besonders reizt. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
            "4": {
                "beruf":   "Kfz-Mechatroniker",
                "group":   "kfz_mechatronik",
                "subject": "Anfrage zur Ausbildung im KFZ Mechatroniker",
                "tags":    ["shop=car_repair", "shop=car", "shop=tyres", "craft=car_repair"],
                "coverage": "good",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung als Kfz-Mechatroniker in Ihrem Unternehmen. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
            "5": {
                "beruf":   "Mechatroniker",
                "group":   "kfz_mechatronik",
                "subject": "Anfrage zur Ausbildung als Mechatroniker",
                "tags":    ["craft=electrician", "craft=car_repair"],
                "coverage": "weak",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Mechatroniker in Ihrem Unternehmen, da mich die Kombination aus Mechanik, Elektronik und Steuerungstechnik besonders interessiert. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
        },
    },
    "3": {
        "label": "Handwerk",
        "berufe": {
            "1": {
                "beruf":   "Maurer",
                "group":   "bau",
                "subject": "Anfrage zur Ausbildung als Maurer",
                "tags":    ["craft=mason", "craft=stonemason"],
                "coverage": "weak",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Maurer in Ihrem Betrieb, da mich handwerkliche Arbeit auf der Baustelle sehr reizt. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
            "2": {
                "beruf":   "Bauzeichner",
                "group":   "bauzeichner",
                "subject": "Anfrage zur Ausbildung als Bauzeichner",
                "tags":    ["office=architect", "office=engineer"],
                "coverage": "weak",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Bauzeichner in Ihrem Büro, da mich technisches Zeichnen und die Planung von Bauprojekten sehr interessieren. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
            "3": {
                "beruf":   "Strassenbauer",
                "group":   "bau",
                "subject": "Anfrage zur Ausbildung als Straßenbauer",
                "tags":    ["craft=building_construction", "office=construction"],
                "coverage": "weak",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Straßenbauer in Ihrem Unternehmen, da mich die Arbeit im Freien und der Aufbau von Infrastruktur motivieren. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
        },
    },
    "4": {
        "label": "Gastronomie",
        "berufe": {
            "1": {
                "beruf":   "Restaurantfachmann-frau",
                "group":   "restaurantfachmann",
                "subject": "Anfrage zur Ausbildung als Restaurantfachmann/-frau",
                "tags":    ["amenity=restaurant", "tourism=hotel"],
                "coverage": "good",
                "body": """\
Sehr geehrte Damen und Herren,

ich schreibe Ihnen aus Marokko und interessiere mich für eine Ausbildung zum Restaurantfachmann in Ihrem Haus, da mir der direkte Kontakt zu Gästen und professioneller Service besonders wichtig sind. Ich habe das B1-Zertifikat und lerne aktuell weiter auf B2-Niveau. Für die Ausbildung 2027 bin ich bereit, nach Deutschland umzuziehen.

Bieten Sie noch einen Ausbildungsplatz für 2027 an? Ich sende Ihnen gerne meine vollständigen Unterlagen.

Mit freundlichen Grüßen
{name}
""",
            },
        },
    },
}

# Flat lookup: beruf name -> beruf dict.
ALL_BERUFE = {b["beruf"]: b for cat in CATEGORIES.values() for b in cat["berufe"].values()}
