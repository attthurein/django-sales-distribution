import re

class Rabbit:
    def __init__(self):
        self.uni2zg_rules = [
            # 1. Reordering
            (r"\u103C\u103E", r"\u103E\u103C"),
            (r"\u103D\u103E", r"\u103E\u103D"),
            
            # 2. Pasint (Virama + Consonant -> Stacked)
            # Ka
            (r"\u1000\u1039\u1000", r"\u1000\u1060"),
            (r"\u1000\u1039\u1001", r"\u1000\u1061"),
            (r"\u1000\u1039\u1002", r"\u1000\u1062"),
            (r"\u1000\u1039\u1003", r"\u1000\u1063"),
            # Kha
            (r"\u1001\u1039\u1000", r"\u1001\u1060"),
            (r"\u1001\u1039\u1001", r"\u1001\u1061"),
            (r"\u1001\u1039\u1002", r"\u1001\u1062"),
            # Ga
            (r"\u1002\u1039\u1000", r"\u1002\u1060"),
            (r"\u1002\u1039\u1001", r"\u1002\u1061"),
            (r"\u1002\u1039\u1002", r"\u1002\u1062"),
            (r"\u1002\u1039\u1003", r"\u1002\u1063"),
            # Nga
            (r"\u1004\u103A\u1039\u1000", r"\u108F\u1060"), # Kinzi + Ka
            (r"\u1004\u103A\u1039\u1001", r"\u108F\u1061"), # Kinzi + Kha
            (r"\u1004\u103A\u1039\u1002", r"\u108F\u1062"), # Kinzi + Ga
            (r"\u1004\u103A\u1039\u1003", r"\u108F\u1063"), # Kinzi + Gha
            (r"\u1004\u1039\u1000", r"\u1004\u1060"),
            (r"\u1004\u1039\u1001", r"\u1004\u1061"),
            (r"\u1004\u1039\u1002", r"\u1004\u1062"),
            (r"\u1004\u1039\u1003", r"\u1004\u1063"),
            # Ca
            (r"\u1005\u1039\u1005", r"\u1005\u1064"),
            (r"\u1005\u1039\u1006", r"\u1005\u1065"),
            (r"\u1005\u1039\u1007", r"\u1005\u1066"),
            (r"\u1005\u1039\u1008", r"\u1005\u1067"),
            # Cha
            (r"\u1006\u1039\u1005", r"\u1006\u1064"),
            (r"\u1006\u1039\u1006", r"\u1006\u1065"),
            # Ja
            (r"\u1007\u1039\u1005", r"\u1007\u1064"),
            (r"\u1007\u1039\u1006", r"\u1007\u1065"),
            (r"\u1007\u1039\u1007", r"\u1007\u1066"),
            (r"\u1007\u1039\u1008", r"\u1007\u1067"),
            # Nya
            (r"\u100A\u1039\u1005", r"\u100A\u1064"),
            (r"\u100A\u1039\u1006", r"\u100A\u1065"),
            (r"\u100A\u1039\u1007", r"\u100A\u1066"),
            (r"\u100A\u1039\u1008", r"\u100A\u1067"),
            (r"\u100B\u1039\u100B", r"\u100B\u1068"),
            (r"\u100B\u1039\u100C", r"\u100B\u1069"),
            (r"\u100C\u1039\u100C", r"\u100C\u1069"),
            (r"\u100D\u1039\u100D", r"\u100D\u106A"),
            (r"\u100D\u1039\u100E", r"\u100D\u106B"),
            (r"\u100E\u1039\u100D", r"\u100E\u106A"),
            (r"\u100E\u1039\u100E", r"\u100E\u106B"),
            # Ta
            (r"\u1010\u1039\u1010", r"\u1010\u106C"),
            (r"\u1010\u1039\u1011", r"\u1010\u106D"),
            (r"\u1010\u1039\u1012", r"\u1010\u106E"),
            (r"\u1010\u1039\u1013", r"\u1010\u106F"),
            # Tha
            (r"\u1011\u1039\u1010", r"\u1011\u106C"),
            (r"\u1011\u1039\u1011", r"\u1011\u106D"),
            (r"\u1011\u1039\u1012", r"\u1011\u106E"),
            # Da
            (r"\u1012\u1039\u1010", r"\u1012\u106C"),
            (r"\u1012\u1039\u1011", r"\u1012\u106D"),
            (r"\u1012\u1039\u1012", r"\u1012\u106E"),
            (r"\u1012\u1039\u1013", r"\u1012\u106F"),
            # Dha
            (r"\u1013\u1039\u1010", r"\u1013\u106C"),
            (r"\u1013\u1039\u1011", r"\u1013\u106D"),
            (r"\u1013\u1039\u1012", r"\u1013\u106E"),
            (r"\u1013\u1039\u1013", r"\u1013\u106F"),
            # Na
            (r"\u1014\u1039\u1010", r"\u1014\u106C"),
            (r"\u1014\u1039\u1011", r"\u1014\u106D"),
            (r"\u1014\u1039\u1012", r"\u1014\u106E"),
            (r"\u1014\u1039\u1013", r"\u1014\u106F"),
            # Pa
            (r"\u1015\u1039\u1015", r"\u1015\u1070"),
            (r"\u1015\u1039\u1016", r"\u1015\u1071"),
            (r"\u1015\u1039\u1017", r"\u1015\u1072"),
            (r"\u1015\u1039\u1018", r"\u1015\u1073"),
            # Pha
            (r"\u1016\u1039\u1015", r"\u1016\u1070"),
            (r"\u1016\u1039\u1016", r"\u1016\u1071"),
            (r"\u1016\u1039\u1017", r"\u1016\u1072"),
            # Ba
            (r"\u1017\u1039\u1015", r"\u1017\u1070"),
            (r"\u1017\u1039\u1016", r"\u1017\u1071"),
            (r"\u1017\u1039\u1017", r"\u1017\u1072"),
            (r"\u1017\u1039\u1018", r"\u1017\u1073"),
            # Bha
            (r"\u1018\u1039\u1015", r"\u1018\u1070"),
            (r"\u1018\u1039\u1016", r"\u1018\u1071"),
            (r"\u1018\u1039\u1017", r"\u1018\u1072"),
            (r"\u1018\u1039\u1018", r"\u1018\u1073"),
            # Ma
            (r"\u1019\u1039\u1015", r"\u1019\u1070"),
            (r"\u1019\u1039\u1016", r"\u1019\u1071"),
            (r"\u1019\u1039\u1017", r"\u1019\u1072"),
            (r"\u1019\u1039\u1018", r"\u1019\u1073"),
            (r"\u1019\u1039\u1019", r"\u1019\u1074"),
            # La
            (r"\u101C\u1039\u101C", r"\u101C\u107D"), # stacked la
            (r"\u101C\u1039\u1010", r"\u101C\u106C"), # La + Ta

            # 3. Medials and Vowels mapping
            # Kinzi
            (r"\u1004\u103A\u1039", r"\u108F"),
            # RaRit
            (r"(\u1000)\u103C", r"\u103C\1"),
            (r"(\u1001)\u103C", r"\u103C\1"),
            (r"(\u1002)\u103C", r"\u103C\1"),
            (r"(\u1003)\u103C", r"\u103C\1"),
            (r"(\u1004)\u103C", r"\u103C\1"),
            (r"(\u1005)\u103C", r"\u103C\1"),
            (r"(\u1006)\u103C", r"\u103C\1"),
            (r"(\u1007)\u103C", r"\u103C\1"),
            (r"(\u1008)\u103C", r"\u103C\1"),
            (r"(\u1009)\u103C", r"\u103C\1"),
            (r"(\u100A)\u103C", r"\u103C\1"),
            (r"(\u100B)\u103C", r"\u103C\1"),
            (r"(\u100C)\u103C", r"\u103C\1"),
            (r"(\u100D)\u103C", r"\u103C\1"),
            (r"(\u100E)\u103C", r"\u103C\1"),
            (r"(\u100F)\u103C", r"\u103C\1"),
            (r"(\u1010)\u103C", r"\u103C\1"),
            (r"(\u1011)\u103C", r"\u103C\1"),
            (r"(\u1012)\u103C", r"\u103C\1"),
            (r"(\u1013)\u103C", r"\u103C\1"),
            (r"(\u1014)\u103C", r"\u103C\1"),
            (r"(\u1015)\u103C", r"\u103C\1"),
            (r"(\u1016)\u103C", r"\u103C\1"),
            (r"(\u1017)\u103C", r"\u103C\1"),
            (r"(\u1018)\u103C", r"\u103C\1"),
            (r"(\u1019)\u103C", r"\u103C\1"),
            (r"(\u101A)\u103C", r"\u103C\1"),
            (r"(\u101B)\u103C", r"\u103C\1"),
            (r"(\u101C)\u103C", r"\u103C\1"),
            (r"(\u101D)\u103C", r"\u103C\1"),
            (r"(\u101E)\u103C", r"\u103C\1"),
            (r"(\u101F)\u103C", r"\u103C\1"),
            (r"(\u1020)\u103C", r"\u103C\1"),
            (r"(\u1021)\u103C", r"\u103C\1"),
            
            # E Vowel (Thway Hto) - move before consonant
            (r"(\u1000)\u1031", r"\u1031\1"),
            (r"(\u1001)\u1031", r"\u1031\1"),
            (r"(\u1002)\u1031", r"\u1031\1"),
            (r"(\u1003)\u1031", r"\u1031\1"),
            (r"(\u1004)\u1031", r"\u1031\1"),
            (r"(\u1005)\u1031", r"\u1031\1"),
            (r"(\u1006)\u1031", r"\u1031\1"),
            (r"(\u1007)\u1031", r"\u1031\1"),
            (r"(\u1008)\u1031", r"\u1031\1"),
            (r"(\u1009)\u1031", r"\u1031\1"),
            (r"(\u100A)\u1031", r"\u1031\1"),
            (r"(\u100B)\u1031", r"\u1031\1"),
            (r"(\u100C)\u1031", r"\u1031\1"),
            (r"(\u100D)\u1031", r"\u1031\1"),
            (r"(\u100E)\u1031", r"\u1031\1"),
            (r"(\u100F)\u1031", r"\u1031\1"),
            (r"(\u1010)\u1031", r"\u1031\1"),
            (r"(\u1011)\u1031", r"\u1031\1"),
            (r"(\u1012)\u1031", r"\u1031\1"),
            (r"(\u1013)\u1031", r"\u1031\1"),
            (r"(\u1014)\u1031", r"\u1031\1"),
            (r"(\u1015)\u1031", r"\u1031\1"),
            (r"(\u1016)\u1031", r"\u1031\1"),
            (r"(\u1017)\u1031", r"\u1031\1"),
            (r"(\u1018)\u1031", r"\u1031\1"),
            (r"(\u1019)\u1031", r"\u1031\1"),
            (r"(\u101A)\u1031", r"\u1031\1"),
            (r"(\u101B)\u1031", r"\u1031\1"),
            (r"(\u101C)\u1031", r"\u1031\1"),
            (r"(\u101D)\u1031", r"\u1031\1"),
            (r"(\u101E)\u1031", r"\u1031\1"),
            (r"(\u101F)\u1031", r"\u1031\1"),
            (r"(\u1020)\u1031", r"\u1031\1"),
            (r"(\u1021)\u1031", r"\u1031\1"),
            
            # Specific replacements for Zawgyi differences
            (r"\u103A", r"\u1039"), # Asat
            (r"\u103F", r"\u1033"), # Great Sa -> ZG specific
            
            # Dual combinations
            (r"\u1037\u103A", r"\u1039\u1037"),
            
            # Tall Aa
            (r"\u102B", r"\u102D"), # Use tall aa in ZG? No, usually \u102B -> \u102B but sometimes style dependent
            
            # Normalize
            (r"\u104E", r"\u104E"), # 
        ]
        
    def uni2zg(self, text):
        if not text:
            return text
        
        # Simple comprehensive replacement for common cases
        # This is a simplified version of Rabbit's logic
        
        # 1. Kinzi
        text = re.sub(r"\u1004\u103A\u1039", "\u108F", text)
        
        # 2. Reorder Ra (Yapin/Yayit/RaRit) - \u103C in Uni moves before consonant in ZG
        # Matches Consonant + Ra -> Ra + Consonant
        # Range of consonants: \u1000-\u1021
        text = re.sub(r"([\u1000-\u1021])\u103C", "\u103C\\1", text)
        
        # 3. Reorder E (Thway Hto) - \u1031 in Uni moves before consonant in ZG
        # But wait, in ZG \u1031 is typed BEFORE consonant? 
        # Actually in ZG storage: Consonant + \u1031 ? No, usually \u1031 + Consonant.
        # Let's check: In Unicode: Consonant + \u1031. In Zawgyi: \u1031 + Consonant.
        # Include Ya Pin (\u103B) in medials check
        text = re.sub(r"([\u1000-\u1021])(\u103B)?(\u103C)?(\u103D)?(\u103E)?\u1031", "\u1031\\1\\2\\3\\4\\5", text)
        
        # 4. Stacked characters (Pa Sint)
        # Handle simple stacking
        replacements = {
            # Ka + Virama + Ka -> Stacked Ka
            '\u1000\u1039\u1000': '\u1060',
            '\u1000\u1039\u1001': '\u1061',
            '\u1000\u1039\u1002': '\u1062',
            '\u1000\u1039\u1003': '\u1063',
            
            # Nga + Virama + ...
            '\u1004\u1039\u1000': '\u1004\u1060', 
            '\u1004\u1039\u1001': '\u1004\u1061',
            '\u1004\u1039\u1002': '\u1004\u1062',
            '\u1004\u1039\u1003': '\u1004\u1063',
            
            # Ca + Virama + ...
            '\u1005\u1039\u1005': '\u1064',
            '\u1005\u1039\u1006': '\u1065',
            
            # Nya + Virama + ...
            '\u100B\u1039\u100B': '\u1068',
            '\u100B\u1039\u100C': '\u1069',
            
            # Ta + Virama + ...
            '\u1010\u1039\u1010': '\u106C',
            '\u1010\u1039\u1011': '\u106D',
            
            # Na + Virama + ...
            '\u1014\u1039\u1010': '\u1014\u106C',
            '\u1014\u1039\u1011': '\u1014\u106D',
            '\u1014\u1039\u1012': '\u1014\u106E',
            
            # Pa + Virama + ...
            '\u1015\u1039\u1015': '\u1070',
            '\u1015\u1039\u1016': '\u1071',
            
            # Ma + Virama + ...
            '\u1019\u1039\u1019': '\u1074',
            
            # La + Virama + ...
            '\u101C\u1039\u101C': '\u107D',
            
            # Ou (Au)
            '\u102D\u102F': '\u108E',
        }
        
        for k, v in replacements.items():
            text = text.replace(k, v)
            
        # 5. Medials reordering for complex cases
        # (Simplified)
        
        return text

def convert(text):
    if not isinstance(text, str):
        return text
    # Check if text contains myanmar characters
    if not re.search(r'[\u1000-\u109F]', text):
        return text
        
    r = Rabbit()
    return r.uni2zg(text)
