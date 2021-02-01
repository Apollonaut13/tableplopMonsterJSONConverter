import json
import os

with open('srd5eMonsters.json') as monsterFile:
    monsters = json.load(monsterFile)
monsterFile.close()

with open('DND5eSRDMonstersForTablePlop.json', 'w+') as tpMonstersFile:
    monsterCollection = {"DND5eSRDMonsters": []}
    for monster in monsters:
        convertedMonster = {
            "stats": {},
            "info": {},
            "appearances": {},
            "savedMessages": {}
        }
        stats = convertedMonster["stats"]

        CR_int = 0
        if '/' not in monster["challenge_rating"]:
            CR_int = int(monster["challenge_rating"])
        proficiencyBonus = 2 + CR_int // 4

        for stat in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]:
            stats[stat] = {
                "expression": f"floor (({stat}-score - 10) / 2)",
                "type": "ability",
                "value": (monster[stat] - 10) // 2,
                "section": "abilities",
                "roll": f"{stat} check: {{1d20 + {stat}}}"
            }
            stats[f"{stat}-score"] = {
                "parent": stat,
                "value": monster[stat],
                "type": "number",
                "hidden": True
            }
            stats[f"{stat}-save"] = {
                "expression": f"{stat} + ({stat}-save-proficiency ? proficiency : 0)",
                "value": monster[f"{stat}_save"] if f"{stat}_save" in monster.keys() else stats[stat]["value"],
                "type": "saving-throw",
                "section": "saving-throws",
                "roll": f"{stat[:3].upper()} save: {{1d20 + {stat}-save}}"
            }
            stats[f"{stat}-save-proficiency"] = {
                "parent": f"{stat}-save",
                "value": f"{stat}_save" in monster.keys(),
                "type": "checkbox",
                "hidden": True
            }
        skills = {
            'athletics': 'dexterity',
            'acrobatics': 'dexterity',
            'sleight-of-hand': 'dexterity',
            'stealth': 'dexterity',
            'arcana': 'intelligence',
            'history': 'intelligence',
            'investigation': 'intelligence',
            'nature': 'intelligence',
            'religion': 'intelligence',
            'animal-handling': 'wisdom',
            'insight': 'wisdom',
            'medicine': 'wisdom',
            'perception': 'wisdom',
            'survival': 'wisdom',
            'deception': 'charisma',
            'intimidation': 'charisma',
            'performance': 'charisma',
            'persuasion': 'charisma'
        }
        for skill, relevant_stat in skills.items():
            try:
                monsterSkillBonus = monster[skill.replace('-', '_')]
            except KeyError:
                monsterSkillBonus = stats[relevant_stat]["value"]

            stats[skill] = {
                "expression": f"{relevant_stat} + ({skill}-expertise ? proficiency*2 : {skill}-proficiency ? proficiency : jack-of-all-trades ? (floor (proficiency / 2)) : 0)",
                "value": monsterSkillBonus,
                "subtitle": relevant_stat[:3],
                "type": "skill",
                "section": "skills",
                "roll": f"{skill.capitalize()} check: {{1d20 + {skill}}}"
            }
            proficient = (monsterSkillBonus - stats[relevant_stat]["value"]) == proficiencyBonus
            expert = (monsterSkillBonus - stats[relevant_stat]["value"]) == (proficiencyBonus * 2)
            stats[f"{skill}-proficiency"] = {
                "value": proficient or expert,
                "type": "checkbox",
                "hidden": True,
                "parent": skill
            }
            stats[f"{skill}-expertise"] = {
                "value": expert,
                "type": "checkbox",
                "hidden": True,
                "parent": skill
            }
        stats["jack-of-all-trades"] = {
            "value": False,
            "type": "checkbox",
            "section": "skills"
        }

        darkVisionValue = 0
        if 'darkvision' in monster['senses']:
            senses = monster['senses'].split()
            darkVisionValue = int(senses[senses.index('darkvision') + 1])
        stats["dark-vision"] = {
            "value": darkVisionValue,
            "type": "number",
            "section": "senses"
        }
        stats["passive-perception"] = {
            "value": 10 + stats['perception']['value'],
            "type": "number",
            "section": "senses",
            "expression": "10 + perception"
        }
        stats["passive-insight"] = {
            "value": 10 + stats['insight']['value'],
            "type": "number",
            "section": "senses",
            "expression": "10 + insight"
        }
        stats["passive-stealth"] = {
            "value": 10 + stats['stealth']['value'],
            "type": "number",
            "section": "senses",
            "expression": "10 + stealth"
        }
        stats["spell-slots-used"] = {
            "type": "checkboxes",
            "max": len(monster['spells']) if 'spells' in monster.keys() else 0,
            "value": 0,
            "section": "spells"
        }
        stats["spell-slots-used-max"] = {
            "type": "number",
            "value": len(monster['spells']) if 'spells' in monster.keys() else 0,
            "parent": "spell-slots-used",
            "hidden": True
        }

        casterLevel = CR_int
        try:
            specials = monster["special_abilities"]
            for special in specials:
                if special["name"] == "Spellcasting":
                    if "-level" in special["desc"]:
                        text = special["desc"].split("-level")[0]
                        casterLevel = int(text.split()[-1][:-2])
                        # print(f"{monster['name']} is a level {casterLevel} spellcaster.")
        except KeyError:
            pass
        stats["level"] = {
            "value": casterLevel,
            "section": "info",
            "type": "number"
        }
        stats["hit-points-maximum"] = {
            "value": monster["hit_points"],
            "section": "info",
            "type": "number",
            "hidden": True,
            "parent": "hit-points",
            "local": True
        }
        stats["hit-points"] = {
            "value": monster["hit_points"],
            "section": "info",
            "type": "health",
            "local": True
        }
        stats["hit-points-temporary"] = {
            "value": 0,
            "section": "info",
            "type": "number",
            "local": True,
            "hidden": True,
            "parent": "hit-points"
        }
        stats["armor-class"] = {
            "value": monster['armor_class'],
            "section": "info",
            "type": "number"
        }
        if len(monster['damage_immunities']) > 0:
            stats['immune-to'] = {
                'value': monster['damage_immunities'],
                'section': 'info',
                'type': 'text'
            }
        if len(monster['damage_resistances']) > 0:
            stats['resistant-to'] = {
                'value': monster['damage_resistances'],
                'section': 'info',
                'type': 'text'
            }
        if len(monster['damage_vulnerabilities']) > 0:
            stats['vulnerable-to'] = {
                'value': monster['damage_vulnerabilities'],
                'section': 'info',
                'type': 'text'
            }
        stats['roll-hp'] = {
            'value': monster['hit_dice'],
            'section': 'info',
            'type': 'text',
            'roll': f"{{roll-hp = {monster['hit_dice']}}} {{hit-points-maximum = roll-hp}} {{hit-points = hit-points-maximum}}"
        }
        stats["size"] = {
            "value": monster['size'],
            "section": "info",
            "type": "text"
        }
        stats["monster-type"] = {
            "value": monster['type'] + (f" ({monster['subtype']})" if len(monster['subtype']) > 0 else ''),
            "section": "info",
            "type": "text"
        }
        stats["alignment"] = {
            "value": monster['alignment'],
            "section": "info",
            "type": "text"
        }
        for movementType, movementSpeed in monster['speed_json'].items():
            if movementType == 'hover':
                stats[f"{movementType}-fly-speed"] = {
                    'value': monster['speed_json']['fly'],
                    'section': 'info',
                    'type': 'number'
                }
            elif (movementType == 'fly') and 'hover' in monster['speed_json'].keys():
                continue
            else:
                stats[f"{movementType}-speed"] = {
                    'value': movementSpeed,
                    'section': 'info',
                    'type': 'number'
                }

        stats["proficiency"] = {
            "value": proficiencyBonus,
            "expression": "2+floor(level/4)",
            "section": "info",
            "type": "number"
        }
        stats["initiative"] = {
            "value": stats['dexterity']['value'],
            "section": "info",
            "type": "number",
            "roll": "!r initiative = 1d20 + initiative"
        }

        info = convertedMonster['info']
        info['description'] = f"<p>{monster['name']}</p>"

        monsterDesc = f"Senses: {monster['senses']}\n\nLanguages: {monster['languages'] if len(monster['languages']) > 0 else '-'}"
        monsterDesc += f"\n\nCR: {monster['challenge_rating']}"
        monsterDesc += f"\n\nCondition Immunities: {monster['condition_immunities']}" if len(
            monster['condition_immunities']) > 0 else ""

        info['notes'] = f"<p><b>Senses:</b> {monster['senses']}</p>" \
                        f"<p><b>Languages:</b> {monster['languages'] if len(monster['languages']) > 0 else '-'}</p>" \
                        f"<p><b>CR:</b> {monster['challenge_rating']}</p>" \
                        f"<p><b>Condition Immunities:</b> {monster['condition_immunities'] if len(monster['condition_immunities']) > 0 else ''}</p>"

        info['sections'] = [
            {
                "name": "abilities",
                "position": "left",
                "tab": 1
            },
            {
                "name": "info",
                "position": "left",
                "tab": 1
            },
            {
                "name": "details",
                "position": "left",
                "tab": 3
            },
            {
                "name": "saving-throws",
                "position": "right",
                "tab": 2
            },
            {
                "name": "senses",
                "position": "right",
                "tab": 2
            },
            {
                "name": "skills",
                "position": "right",
                "tab": 2
            },
            {
                "name": "actions",
                "position": "bottom",
                "tab": 4,
                "savedMessages": True
            },
            {
                "name": "spells",
                "position": "bottom",
                "tab": 4,
                "savedMessages": True
            }
        ]
        convertedMonster['appearances'] = [f"https://5e.tools/img/MM/{monster['name'].replace(' ', '%20')}.png"]
        convertedMonster['savedMessages'] = []

        if 'actions' in monster.keys():
            for action in monster['actions']:
                convertedAction = {}
                convertedAction['name'] = action['name']
                if action['attack_bonus'] == 0:
                    convertedAction['message'] = action['desc']
                else:
                    attackMessage = f"{action['name']}, {' '.join(action['desc'].lower().split()[:3])} "  # Slam, melee weapon attack:
                    # print(monster['name'])
                    attackMessage += f"{{1d20 + {action['attack_bonus']}}} to hit"
                    try:
                        words = action['desc'].split()
                        hitIndex = words.index('Hit:')
                        avgDamage = int(words[hitIndex + 1])
                        attackMessage += f", {{{action['damage_dice'] if 'damage_dice' in action.keys() else 0} + {action['damage_bonus'] if 'damage_bonus' in action.keys() else 0}}} (average {avgDamage}) {' '.join(action['desc'].split()[-2:]) if action['desc'].endswith('damage.') else ''}"
                    except ValueError:
                        pass
                    convertedAction['message'] = attackMessage
                convertedAction['section'] = 'actions'
                convertedMonster['savedMessages'].append(convertedAction)

        monsterCollection["DND5eSRDMonsters"].append(convertedMonster)

        with open(f"./tableplopMonsters/{monster['name'].replace('/', '')}.json", 'w') as newFile:
            json.dump(convertedMonster, newFile)
        newFile.close()
    json.dump(monsterCollection, tpMonstersFile)
tpMonstersFile.close()
