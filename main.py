import json
from concurrent.futures import ThreadPoolExecutor
from config.persona import PERSONA_DICT
from agents.area_chair import AreaChair
from agents.reviewer import Reviewer


def main(paper_name):

    # 1. 实例化
    ac = AreaChair("0", PERSONA_DICT["area_chair"])
    r1 = Reviewer("1", PERSONA_DICT["logical_reviewer"])
    r2 = Reviewer("2", PERSONA_DICT["empirical_reviewer"])
    r3 = Reviewer("3", PERSONA_DICT["statistical_reviewer"])
    r4 = Reviewer("4", PERSONA_DICT["reproducibility_reviewer"])
    reviewers = [r1, r2, r3, r4]

    # 2. 加载论文
    paper_path = f"papers/{paper_name}"
    content = ac.load_paper(paper_path)
    for r in reviewers:
        r.load_paper(content)

    # 3. 审稿
    reviews = {}
    with ThreadPoolExecutor(max_workers=len(reviewers)) as executor:
        future_to_reviewer = {executor.submit(r.independent_review): r.reviewer_id for r in reviewers}

        for future in future_to_reviewer:
            r_id = future_to_reviewer[future]
            try:
                reviews[r_id] = future.result()
            except Exception as e:
                return "Error! {}".format(e)

    # 4. 汇总
    feedback = ac.synthesize_feedback(reviews)

    # 5. 保存
    with open(f'Review of {paper_name}.json', 'w') as f:
        json.dump(feedback, f, ensure_ascii=False, indent=4)


if __name__ == "__main__":

    paper_name = "A study on emotion recognition of autistic children integrating emotional intelligence and behavior analysis.pdf"
    main(paper_name)
