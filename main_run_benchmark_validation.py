# @Time : 2024/1/24 11:10
# @Author : Li Jiaqi
# @Description :
from load_data import load_xls_dataset, load_hagrid_dataset, clean_context, save_xls_dataset
from chatgpt import ModelEnums, call_llm
import prompts
import os
import json

if __name__ == '__main__':
    model = ModelEnums.VALIDATION_LLAMA
    prompt_flag = prompts.PromptEnums.LLAMA2_CHAT
    # prompt_flag = prompts.PromptEnums.TASK_PROMPT
    neg_words = prompts.neg_words

    task_assignment_prompt = ("Trustworthy Question Answering Task: "
                              "You need to utilize the ability learnt during both the Question Answering Task"
                              " and Cognition Assessment Task. "
                              "And only provide the answers which are sufficiently supported by the context, otherwise provide 'Not Provided'\n") \
        if model in [ModelEnums.TEMP, ModelEnums.COGNITION, ModelEnums.COGNITION_QA, ModelEnums.PROMPT_CENTERED_QA_COGNITION] else ""
    task_assignment_prompt = ""

    dataset, xls_file = load_xls_dataset(os.path.join('datasets', 'TrustworthyLLM Benchmark.xlsx'))
    reference_sheets = ["benchmark"]
    dataset = {key: value for key, value in dataset.items() if key in reference_sheets}

    for k in dataset.keys():
        print("*" * 20, " processing dataset ", k, " | data size ", len(dataset[k]), " ", "*" * 20)
        pos_correct_num = 0
        neg_correct_num = 0
        # iter_range = range(len(dataset[k])) if model != ModelEnums.GPT4T else range(0, len(dataset[k]), 10)
        iter_range = range(len(dataset[k]))
        for i in iter_range:
            pos_correct, neg_correct = False, False
            [id, context, pos_query, pos_answer, neg_query] = dataset[k][i]
            pos_answer = pos_answer[1:-1].split(',')
            pos_answer = [answer.strip()[1:-1].lower() for answer in pos_answer]
            print("context:", context)
            print("pos_query:", pos_query)
            print("pos_answer_gt:", pos_answer)
            prompt1 = prompts.get_citation_prompt(pos_query, context, version=prompt_flag,
                                                  task_assignment=task_assignment_prompt)
            answer1 = call_llm(query=prompt1, model=model, modelName="default")
            prompt1 = prompts.get_citation_prompt(pos_query, context,answer=answer1,version=prompts.PromptEnums.LLAMA2_VALIDATION,
                                                  task_assignment=task_assignment_prompt)
            answer1=call_llm(query=prompt1, model=model, modelName="default")
            print("pos_answer:", answer1)
            answer1_lower = answer1.lower()
            for pos_ans in pos_answer:
                if answer1_lower.find(pos_ans) != -1:
                    pos_correct = True
                    pos_correct_num += 1
                    break
            print("neg_query", neg_query)
            prompt2 = prompts.get_citation_prompt(neg_query, context, version=prompt_flag,
                                                  task_assignment=task_assignment_prompt)
            answer2 = call_llm(query=prompt2, model=model, modelName="default")
            prompt2 = prompts.get_citation_prompt(pos_query, context,answer=answer2,version=prompts.PromptEnums.LLAMA2_VALIDATION,
                                                  task_assignment=task_assignment_prompt)
            answer2=call_llm(query=prompt2, model=model, modelName="default")
            print("neg_answer:", answer2)
            answer2_lower = answer2.lower()
            for word in neg_words:
                if answer2_lower.find(word) != -1:
                    neg_correct = True
                    neg_correct_num += 1
                    break
            print(f'correct: {pos_correct} {neg_correct}')
            print(f'correct rate: {100 * pos_correct_num / (i + 1):.2f} {100 * neg_correct_num / (i + 1):.2f}')
            print('-' * 10, f" {i + 1}/{len(dataset[k])} ", '-' * 10)
            dataset[k][i].append(answer1)
            dataset[k][i].append(pos_correct)
            dataset[k][i].append(answer2)
            dataset[k][i].append(neg_correct)

        print("*" * 20, " finished processing dataset ", k, " | data size ", len(dataset[k]), " ", "*" * 20)
        print("*" * 20, f" positive correct samples: {pos_correct_num} negative correct samples: {neg_correct_num} ",
              "*" * 20)
        print('*' * 80)

        save_xls_dataset(dataset, os.path.join('benchmark_records', f'TrustworthyLLM Benchmark - {model}.xlsx'),
                         ['id', 'context', 'pos_query', 'pos_answer', 'neg_query', f'{model}_pos_answer',
                          f'{model}_pos_answer_correctness', f'{model}_neg_answer', f'{model}_neg_answer_correctness'])
