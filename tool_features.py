from __future__ import annotations

import json
from typing import Any

HARRY_POTTER_CHARACTERS = [
    "Harry James Potter",
    "Hermione Jean Granger",
    "Ron Weasley",
    "Fred Weasley",
    "George Weasley",
    "Bill Weasley",
    "Percy Weasley",
    "Charlie Weasley",
    "Ginny Weasley",
    "Molly Weasley",
    "Arthur Weasley",
    "Neville Longbottom",
    "Luna Lovegood",
    "Draco Malfoy",
    "Albus Percival Wulfric Brian Dumbledore",
    "Minerva McGonagall",
    "Remus Lupin",
    "Rubeus Hagrid",
    "Sirius Black",
    "Severus Snape",
    "Bellatrix Lestrange",
    "Lord Voldemort",
    "Cedric Diggory",
    "Nymphadora Tonks",
    "James Potter",
]

HARRY_POTTER_CHARACTER_DATA: dict[str, dict[str, Any]] = {
    "Harry James Potter": {
        "summary": "The central hero of the Harry Potter series, known as the Boy Who Lived after surviving Voldemort's attack as a baby.",
        "role": "Wizard, Hogwarts student, and later Auror",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Dumbledore's Army", "Order of the Phoenix"],
        "notable_traits": ["brave", "loyal", "impulsive", "protective"],
    },
    "Hermione Jean Granger": {
        "summary": "Harry Potter's brilliant friend whose intelligence, discipline, and courage often keep the trio alive.",
        "role": "Witch, student leader, and key strategist of the trio",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Dumbledore's Army", "Order of the Phoenix"],
        "notable_traits": ["brilliant", "resourceful", "loyal", "principled"],
    },
    "Ron Weasley": {
        "summary": "Harry's closest male friend, a loyal member of the trio who brings humor, heart, and tactical instincts.",
        "role": "Wizard and Harry Potter's best friend",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Dumbledore's Army", "Order of the Phoenix"],
        "notable_traits": ["loyal", "funny", "brave", "sometimes insecure"],
    },
    "Fred Weasley": {
        "summary": "One of the Weasley twins, famous for fearless pranks and co-founding Weasleys' Wizard Wheezes.",
        "role": "Prankster, entrepreneur, and Order ally",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Weasleys' Wizard Wheezes", "Order of the Phoenix"],
        "notable_traits": ["mischievous", "bold", "clever", "charismatic"],
    },
    "George Weasley": {
        "summary": "Fred's twin brother, a gifted joke-maker and co-founder of Weasleys' Wizard Wheezes.",
        "role": "Prankster, entrepreneur, and Order ally",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Weasleys' Wizard Wheezes", "Order of the Phoenix"],
        "notable_traits": ["mischievous", "inventive", "loyal", "resilient"],
    },
    "Bill Weasley": {
        "summary": "The eldest Weasley brother, a cool-headed curse-breaker for Gringotts who fights Voldemort's forces.",
        "role": "Curse-breaker and Order member",
        "house": "Gryffindor",
        "affiliations": ["Gringotts", "Order of the Phoenix", "Weasley family"],
        "notable_traits": ["capable", "calm", "protective", "adventurous"],
    },
    "Percy Weasley": {
        "summary": "An ambitious Weasley brother whose loyalty to rules and status strains his family relationships for a time.",
        "role": "Ministry official and former Head Boy",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Ministry of Magic", "Weasley family"],
        "notable_traits": ["ambitious", "formal", "rule-driven", "intelligent"],
    },
    "Charlie Weasley": {
        "summary": "The Weasley brother known for working with dragons and living a rugged life in Romania.",
        "role": "Dragon expert",
        "house": "Gryffindor",
        "affiliations": ["Weasley family", "Romanian dragon reserve", "Order of the Phoenix"],
        "notable_traits": ["adventurous", "tough", "independent", "good-natured"],
    },
    "Ginny Weasley": {
        "summary": "The youngest Weasley sibling, a talented witch, fierce fighter, and gifted Quidditch player.",
        "role": "Witch, student leader, and athlete",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Dumbledore's Army", "Order of the Phoenix"],
        "notable_traits": ["confident", "brave", "sharp-witted", "determined"],
    },
    "Molly Weasley": {
        "summary": "The matriarch of the Weasley family, known for her warmth, fierce love, and formidable magical skill.",
        "role": "Parent and Order supporter",
        "affiliations": ["Weasley family", "Order of the Phoenix"],
        "notable_traits": ["nurturing", "protective", "strong-willed", "fearless"],
    },
    "Arthur Weasley": {
        "summary": "The Weasley patriarch, a kind Ministry worker with a deep fascination for Muggle life and objects.",
        "role": "Ministry employee and Order member",
        "affiliations": ["Ministry of Magic", "Order of the Phoenix", "Weasley family"],
        "notable_traits": ["curious", "kind", "eccentric", "principled"],
    },
    "Neville Longbottom": {
        "summary": "A shy student who grows into one of Hogwarts' bravest defenders and a symbol of quiet courage.",
        "role": "Wizard, resistance leader, and later professor",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Dumbledore's Army"],
        "notable_traits": ["brave", "humble", "persistent", "kind"],
    },
    "Luna Lovegood": {
        "summary": "An eccentric Ravenclaw student whose unusual perspective often leads to surprising insight and truth.",
        "role": "Witch and ally of Harry Potter",
        "house": "Ravenclaw",
        "affiliations": ["Hogwarts", "Dumbledore's Army", "Lovegood family"],
        "notable_traits": ["dreamy", "perceptive", "loyal", "fearless"],
    },
    "Draco Malfoy": {
        "summary": "Harry's school rival, raised in a pure-blood supremacist household and pressured by dark forces.",
        "role": "Student and reluctant pawn of Voldemort's circle",
        "house": "Slytherin",
        "affiliations": ["Hogwarts", "Malfoy family", "Slytherin house"],
        "notable_traits": ["proud", "sharp-tongued", "conflicted", "status-conscious"],
    },
    "Albus Percival Wulfric Brian Dumbledore": {
        "summary": "The legendary Hogwarts headmaster whose wisdom, secrecy, and long game define the fight against Voldemort.",
        "role": "Headmaster and leader against Voldemort",
        "affiliations": ["Hogwarts", "Order of the Phoenix", "Wizarding leadership"],
        "notable_traits": ["wise", "strategic", "mysterious", "compassionate"],
    },
    "Minerva McGonagall": {
        "summary": "A respected Hogwarts professor and later headmistress known for discipline, loyalty, and steel under pressure.",
        "role": "Professor, deputy headmistress, and later headmistress",
        "house": "Gryffindor",
        "affiliations": ["Hogwarts", "Order of the Phoenix"],
        "notable_traits": ["strict", "brave", "fair", "deeply loyal"],
    },
    "Remus Lupin": {
        "summary": "A talented Defense Against the Dark Arts professor, werewolf, and one of James Potter's closest friends.",
        "role": "Professor, Marauder, and Order member",
        "affiliations": ["Order of the Phoenix", "Marauders", "Hogwarts"],
        "notable_traits": ["gentle", "intelligent", "self-sacrificing", "reserved"],
    },
    "Rubeus Hagrid": {
        "summary": "Hogwarts' giant-hearted gamekeeper who introduces Harry to the wizarding world and never stops protecting him.",
        "role": "Gamekeeper, professor, and loyal friend",
        "affiliations": ["Hogwarts", "Order of the Phoenix"],
        "notable_traits": ["kind", "loyal", "emotional", "brave"],
    },
    "Sirius Black": {
        "summary": "Harry's godfather, a wrongly imprisoned fugitive, and one of the original Marauders.",
        "role": "Order member and Harry Potter's godfather",
        "affiliations": ["Order of the Phoenix", "Marauders", "Black family"],
        "notable_traits": ["rebellious", "protective", "reckless", "devoted"],
    },
    "Severus Snape": {
        "summary": "A master of potions and deception whose harsh exterior hides one of the saga's most complex loyalties.",
        "role": "Professor, headmaster, and double agent",
        "affiliations": ["Hogwarts", "Order of the Phoenix", "Death Eaters"],
        "notable_traits": ["brilliant", "guarded", "bitter", "deeply committed"],
    },
    "Bellatrix Lestrange": {
        "summary": "One of Voldemort's most dangerous and fanatically loyal followers.",
        "role": "Dark witch and Death Eater",
        "affiliations": ["Death Eaters", "Lestrange family", "Black family"],
        "notable_traits": ["fanatical", "cruel", "chaotic", "fearless"],
    },
    "Lord Voldemort": {
        "summary": "The main antagonist of the series, obsessed with immortality, control, and the conquest of the wizarding world.",
        "role": "Dark wizard and supreme antagonist",
        "affiliations": ["Death Eaters", "Slytherin legacy"],
        "notable_traits": ["ruthless", "calculating", "charismatic", "power-hungry"],
    },
    "Cedric Diggory": {
        "summary": "A well-liked Hufflepuff student remembered for fairness, sportsmanship, and quiet heroism.",
        "role": "Student and Triwizard Champion",
        "house": "Hufflepuff",
        "affiliations": ["Hogwarts", "Hufflepuff house"],
        "notable_traits": ["noble", "fair", "athletic", "kind"],
    },
    "Nymphadora Tonks": {
        "summary": "A gifted Auror and Metamorphmagus whose humor and courage make her a memorable Order member.",
        "role": "Auror and Order member",
        "affiliations": ["Ministry of Magic", "Order of the Phoenix"],
        "notable_traits": ["playful", "brave", "skilled", "warm-hearted"],
    },
    "James Potter": {
        "summary": "Harry's father, an accomplished wizard, Quidditch player, and one of the original Marauders.",
        "role": "Marauder and member of the first Order of the Phoenix",
        "house": "Gryffindor",
        "affiliations": ["Marauders", "Order of the Phoenix", "Potter family"],
        "notable_traits": ["confident", "talented", "loyal", "protective"],
    },
}


def build_image_hints(name: str) -> list[str]:
    return [
        f"{name} Harry Potter portrait",
        f"{name} Harry Potter movie still",
        f"{name} wand costume reference",
    ]


def describe_harry_potter_character(name: str) -> dict[str, Any]:
    if name not in HARRY_POTTER_CHARACTER_DATA:
        raise ValueError(f"Unknown Harry Potter character: {name}")

    result = dict(HARRY_POTTER_CHARACTER_DATA[name])
    result["name"] = name
    result["image_hints"] = build_image_hints(name)
    return result


def normalize_hex_color(color_hex: str) -> str:
    value = color_hex.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    if len(value) != 6 or any(ch not in "0123456789abcdefABCDEF" for ch in value):
        raise ValueError("color_hex must be a valid 3-digit or 6-digit hexadecimal color string.")
    return f"#{value.upper()}"


def suggest_color_names(red: int, green: int, blue: int) -> list[str]:
    if abs(red - green) < 12 and abs(green - blue) < 12:
        if red < 35:
            return ["black", "charcoal", "near-black"]
        if red < 90:
            return ["slate gray", "graphite", "smoky gray"]
        if red < 170:
            return ["gray", "stone", "ash"]
        if red < 225:
            return ["silver", "light gray", "mist"]
        return ["white", "ivory", "snow"]

    if red > 210 and green > 180 and blue < 120:
        return ["gold", "mustard", "amber"]
    if red > 210 and green > 120 and blue < 120:
        return ["orange", "tangerine", "apricot"]
    if red > 190 and blue > 160 and green < 170:
        return ["pink", "rose", "magenta"]
    if red > 140 and green < 110 and blue < 110:
        return ["red", "crimson", "scarlet"]
    if green > 140 and red < 140 and blue < 140:
        return ["green", "emerald", "jade"]
    if blue > 140 and red < 140 and green < 170:
        return ["blue", "azure", "cobalt"]
    if red > 100 and blue > 120 and green < 120:
        return ["purple", "violet", "plum"]
    if red > 90 and green > 60 and blue < 70:
        return ["brown", "chestnut", "copper"]
    if green > 140 and blue > 140 and red < 120:
        return ["cyan", "teal", "aqua"]

    dominant = max((red, "red"), (green, "green"), (blue, "blue"))[1]
    if dominant == "red":
        return ["warm red", "rust", "brick"]
    if dominant == "green":
        return ["sage", "green", "olive"]
    return ["blue", "steel blue", "indigo"]


def rgb_to_hsl(red: int, green: int, blue: int) -> dict[str, float]:
    r = red / 255
    g = green / 255
    b = blue / 255
    max_channel = max(r, g, b)
    min_channel = min(r, g, b)
    delta = max_channel - min_channel
    lightness = (max_channel + min_channel) / 2

    if delta == 0:
        hue = 0.0
        saturation = 0.0
    else:
        saturation = delta / (1 - abs(2 * lightness - 1))
        if max_channel == r:
            hue = ((g - b) / delta) % 6
        elif max_channel == g:
            hue = ((b - r) / delta) + 2
        else:
            hue = ((r - g) / delta) + 4
        hue *= 60

    return {
        "h": round(hue, 1),
        "s": round(saturation * 100, 1),
        "l": round(lightness * 100, 1),
    }


def relative_luminance(red: int, green: int, blue: int) -> float:
    def linearize(channel: int) -> float:
        value = channel / 255
        if value <= 0.04045:
            return value / 12.92
        return ((value + 0.055) / 1.055) ** 2.4

    r = linearize(red)
    g = linearize(green)
    b = linearize(blue)
    return round(0.2126 * r + 0.7152 * g + 0.0722 * b, 4)


def dominant_channel(red: int, green: int, blue: int) -> str:
    return max((red, "red"), (green, "green"), (blue, "blue"))[1]


def color_temperature(red: int, green: int, blue: int) -> str:
    if red > blue + 35:
        return "warm"
    if blue > red + 35:
        return "cool"
    return "balanced"


def recommended_text_color(luminance: float) -> str:
    return "#000000" if luminance > 0.4 else "#FFFFFF"


def name_a_color(color_hex: str) -> dict[str, Any]:
    normalized = normalize_hex_color(color_hex)
    red = int(normalized[1:3], 16)
    green = int(normalized[3:5], 16)
    blue = int(normalized[5:7], 16)
    brightness = round((0.299 * red + 0.587 * green + 0.114 * blue) / 255, 3)
    luminance = relative_luminance(red, green, blue)

    return {
        "color_hex": normalized,
        "rgb": {"r": red, "g": green, "b": blue},
        "hsl": rgb_to_hsl(red, green, blue),
        "brightness": brightness,
        "relative_luminance": luminance,
        "dominant_channel": dominant_channel(red, green, blue),
        "temperature": color_temperature(red, green, blue),
        "suggested_names": suggest_color_names(red, green, blue),
        "recommended_text_color": recommended_text_color(luminance),
    }


DEFAULT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "describe_harry_potter_character",
            "description": (
                "Use this when the user asks about a specific Harry Potter character. "
                "Returns a structured profile with summary, role, affiliations, traits, and image search hints."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "enum": HARRY_POTTER_CHARACTERS,
                        "description": "Exact name of the Harry Potter character to describe.",
                    }
                },
                "required": ["name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "name_a_color",
            "description": (
                "Use this when the user provides a hex color and wants a grounded color profile. "
                "Returns normalized hex, RGB, HSL, brightness, luminance, likely names, warmth, and a readable text color."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "color_hex": {
                        "type": "string",
                        "description": "A hexadecimal color value represented as a string, for example #4F46E5.",
                    }
                },
                "required": ["color_hex"],
            },
        },
    },
]


def parse_tool_arguments(tool_call: dict[str, Any]) -> dict[str, Any]:
    function = tool_call.get("function", {})
    if "arguments_json" in function:
        return function["arguments_json"]

    raw_arguments = function.get("arguments", "").strip()
    if not raw_arguments:
        return {}

    try:
        return json.loads(raw_arguments)
    except json.JSONDecodeError:
        return {"raw_arguments": raw_arguments}


def execute_tool_call(tool_call: dict[str, Any]) -> dict[str, Any]:
    function_name = tool_call["function"]["name"]
    arguments = parse_tool_arguments(tool_call)

    if function_name == "describe_harry_potter_character":
        result = describe_harry_potter_character(arguments["name"])
    elif function_name == "name_a_color":
        result = name_a_color(arguments["color_hex"])
    else:
        raise ValueError(f"Unsupported tool: {function_name}")

    return {
        "tool_call_id": tool_call["id"],
        "name": function_name,
        "arguments": arguments,
        "result": result,
    }


def execute_tool_calls(tool_calls: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tool_results: list[dict[str, Any]] = []
    for tool_call in tool_calls:
        try:
            tool_results.append(execute_tool_call(tool_call))
        except Exception as exc:
            tool_results.append(
                {
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "name": tool_call.get("function", {}).get("name", "unknown"),
                    "arguments": parse_tool_arguments(tool_call),
                    "result": {"error": str(exc)},
                }
            )
    return tool_results


def build_assistant_tool_call_message(tool_calls: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "role": "assistant",
        "content": "",
        "tool_calls": [
            {
                "id": tool_call["id"],
                "type": tool_call["type"],
                "function": {
                    "name": tool_call["function"]["name"],
                    "arguments": tool_call["function"]["arguments"],
                },
            }
            for tool_call in tool_calls
        ],
    }


def build_tool_result_messages(tool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "role": "tool",
            "tool_call_id": tool_result["tool_call_id"],
            "content": json.dumps(tool_result["result"]),
        }
        for tool_result in tool_results
    ]
