DEFAULT_SYSTEM_MSG = (
    "You are an agent are in the process of going through a book series"
    " to create a comprehensive wiki."
    ' Add relevant information from the `Current chunk` to wiki' 
    ' using the various functions given to you.'
    ' You can call multiple multiple functions if needed.'
)

DEFAULT_PROMPT_TEMPLATE = "#Previous chunks:\n\n{prev_chunks} #Current chunk:\n\n{curr_chunk}"

def apply_prev_chunks_template(prev_chunks: list[str]):
    applied = ""
    for chunk in prev_chunks:
        applied += f"```{chunk}```\n\n"
    return applied