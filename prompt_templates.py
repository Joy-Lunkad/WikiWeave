DEFAULT_ADD_SYSTEM_MSG = (
    "You are an agent are in the process of going through a book series"
    " to create a comprehensive wiki."
    " Add relevant information from the `Current chunk` to wiki"
    " using the various functions given to you."
    " Call each function multiple times if needed."
    " Output `do_nothing` function if the current chunk contains only"
    " the index or table of contents."
)

DEFAULT_UPDATE_SYSTEM_MSG = (
    "You are an agent are in the process of creating a comprehensive wiki for a book series."
    " Update the existing content with new information from the buffer according"
    " to the instructions. Your output text must be Markdown formatted if required"
    " by the user. Your writing style must mirror the writing style of popular fan wikis."
    " If no information is presented to you, Output '...'"
    " DONOT assuming missing information, simply skip it and don't mention it." 
)

DEFAULT_PROMPT_TEMPLATE = (
    "#Summary of previous chunks:\n\n{prev_chunks} #Current chunk:\n\n{curr_chunk}"
)


def apply_prev_chunks_template(prev_chunks: list[str]):
    applied = ""
    for chunk in prev_chunks:
        applied += f"```{chunk}```\n\n"
    return applied


UPDATE_FUNCTION_PROMPT_TEMPLATE = (
    'Rewrite the content by combining the new information from the buffer to' 'the existing information of the'
    ' {section_name}: {section_entity_name}\'s {attribute_name}'
    ' according to the update instructions.\n\n'
    'Description of {attribute_name}: """{attribute_description}"""\n\n'
    'Update Instructions: """{update_prompt}\n\n"""'
    'Existing {attribute_name} information: """{existing_data}"""\n\n'
    'New information from {attribute_name} buffer: """{new_data}"""\n\n'
)
