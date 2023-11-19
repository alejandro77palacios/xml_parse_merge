from pathlib import Path
from pprint import pprint

import pandas as pd
from lxml import etree


def extract_attributes(node, attributes):
    return {attribute: node.get(attribute) for attribute in attributes}


def update_key(dictionary, key, number):
    dictionary[key + str(number)] = dictionary.pop(key)


class QuestionParser:
    parser = etree.XMLParser(recover=True)
    namespaces = {'ns': 'http://www.imsglobal.org/xsd/imsqti_v2p1'}

    def __init__(self, file_path: str):
        self.file_path = Path(file_path)
        self.root = etree.parse(self.file_path, parser=self.parser).getroot()
        self.xpaths = {
            'response_declaration': './ns:responseDeclaration',
            'correct_response': './ns:responseDeclaration/ns:correctResponse/ns:value',
            'outcome_declaration': './ns:outcomeDeclaration',
            'choice_interaction': './ns:itemBody/ns:choiceInteraction',
            'question': './ns:itemBody/ns:choiceInteraction/ns:prompt/ns:span',
            'answers': './ns:itemBody/ns:choiceInteraction/ns:simpleChoice/ns:span',
            'response_if': './ns:responseProcessing/ns:responseCondition/ns:responseIf',
            'response_else': './ns:responseProcessing/ns:responseCondition/ns:responseElse',
        }

    def produce_table(self):
        data = self.process_data()
        df = pd.DataFrame(data)
        ordered_columns = ['identifier', 'title', 'adaptive', 'timeDependent', 'identifier2', 'cardinality', 'baseType',
                           'value', 'identifier3', 'cardinality4', 'baseType5', 'responseIdentifier', 'shuffle',
                           'maxChoices', 'question', 'identifier6', 'answer', 'identifier8', 'identifier9',
                           'identifier10', 'baseValue', 'baseType11', 'identifier12', 'baseValue13', 'baseType14']
        return df[ordered_columns]

    def process_data(self):
        answers = self.get_answers()
        data = []
        for code, answer in answers:
            current_data = self.get_root_fields()
            current_data.update(self.get_response_declaration_fields())
            current_data.update(self.get_correct_response())
            current_data.update(self.get_outcome_declaration_fields())
            current_data.update(self.get_choice_interaction_fields())
            current_data.update(self.get_question())
            current_data.update({'identifier6': code, 'answer': answer})
            current_data.update(self.get_match_identifiers())
            current_data.update(self.get_outcome_value_fields())
            current_data.update(self.get_else_fields())
            data.append(current_data)
        return data

    def get_root_fields(self):
        fields = ('title', 'identifier', 'adaptive', 'timeDependent')
        return {field: self.root.get(field) for field in fields}

    def get_response_declaration_fields(self):
        node = self.find_descendant('response_declaration')
        fields = ('identifier', 'cardinality', 'baseType')
        result = extract_attributes(node, fields)
        update_key(result, 'identifier', 2)
        return result

    def get_correct_response(self):
        node = self.find_descendant('correct_response')
        return {'value': node.text}

    def get_outcome_declaration_fields(self):
        node = self.find_descendant('outcome_declaration')
        fields = ('identifier', 'cardinality', 'baseType')
        result = extract_attributes(node, fields)
        for field, num in zip(fields, range(3, 6)):
            update_key(result, field, num)
        return result

    def get_choice_interaction_fields(self):
        node = self.find_descendant('choice_interaction')
        fields = ('responseIdentifier', 'shuffle', 'maxChoices')
        return extract_attributes(node, fields)

    def get_question(self) -> dict:
        node = self.find_descendant('question')
        return {'question': node.text}

    def get_answers(self):
        answers = self.root.xpath('./ns:itemBody/ns:choiceInteraction/ns:simpleChoice', namespaces=self.namespaces)
        if 'true' in self.file_path.name.lower():
            # extract curren text
            texts = [answer.text for answer in answers]
            identifiers = [answer.get('identifier') for answer in answers]
        else:
            texts = [answer.xpath('./ns:span', namespaces=self.namespaces)[0].text for answer in answers]
            identifiers = [answer.get('identifier') for answer in answers]
        return tuple(zip(identifiers, texts))

    def get_match_identifiers(self):
        node = self.find_descendant('response_if')
        match_node = self.find_first_by_xpath('./ns:match', node)
        paths = ('./ns:variable', './ns:correct')
        names = ('identifier8', 'identifier9')
        return {name: self.find_first_by_xpath(path, match_node).get('identifier') for path, name in zip(paths, names)}

    def get_outcome_value_fields(self):
        node = self.find_descendant('response_if')
        outcome_node = self.find_first_by_xpath('./ns:setOutcomeValue', node)
        identifier = outcome_node.get('identifier')
        base_value_node = self.find_first_by_xpath('./ns:baseValue', outcome_node)
        base_value = base_value_node.text
        base_type = base_value_node.get('baseType')
        return {'identifier10': identifier, 'baseValue': base_value, 'baseType11': base_type}

    def get_else_fields(self):
        node = self.find_descendant('response_else')
        outcome_node = self.find_first_by_xpath('./ns:setOutcomeValue', node)
        identifier = outcome_node.get('identifier')
        base_value_node = self.find_first_by_xpath('./ns:baseValue', outcome_node)
        base_value = base_value_node.text
        base_type = base_value_node.get('baseType')
        return {'identifier12': identifier, 'baseValue13': base_value, 'baseType14': base_type}

    ############################## HELPERS ##############################
    def find_descendant(self, element_name: str, base_node=None):
        xpath = self.xpaths[element_name]
        return self.find_first_by_xpath(xpath, base_node)

    def find_first_by_xpath(self, xpath: str, base_node=None):
        if base_node is None:
            base_node = self.root
        return base_node.xpath(xpath, namespaces=self.namespaces)[0]


# response_declarations = root.xpath('./ns:responseDeclaration', namespaces=namespaces)
# len(response_declarations)

if __name__ == '__main__':
    parser = QuestionParser('Q0_Multiple_Choice.xml')
    df = parser.produce_table()
    pprint(df)

# node itemBody / choiceInteraction
# attributes: responseIdentifier, shuffle, maxChoices
