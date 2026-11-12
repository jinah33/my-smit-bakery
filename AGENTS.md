# 프로젝트규칙
## 설명
1. 전문용어는쉬운말로풀어쓴다
2. 파일을바꾸거나명령을실행하기전에할일을세줄이내로먼저설명하고, 바꾼뒤에는무엇을바꿨는지요약한다
## 명세
3. project_spec.md가이프로젝트의기준이다. 명세가바뀌면코드도명세에맞게고치고코드만따로바꾸지않는다
4. 바꾼내용은project_spec.md 끝의변경기록에날짜, 바꾼것, 이유, 결과로남긴다
5. 요청한것만가장단순한방법으로만든다
## 숫자
6. 코딩AI가제안한숫자에는"가정"이라고표시하고, 코드에서는파일맨위한곳에모은다
7. 모르는값은지어내지말고예시를제안한뒤확인한다
## 실행
8. 긴출력은results 폴더에저장하고요약만보여준다
9. 완료라고말하기전에직접실행해확인한다
10. 오류는원인을쉬운말로설명하고고친다
11. 스킬의 긴 절차는 사용자가 요청할 때만 쓴다. 단 오류가 나면 systematic-debugging으로 원인부터 찾고, 완료라고 말하기 전에는 verification-before-completion으로 직접 실행해 확인한다
## 파일이름
12. 파이썬파일과데이터파일이름은영어소문자로, 단어사이는밑줄로쓴다(예: config.py, customer_traits.csv)
## 보안
13. 실제매장데이터원본, API 키, 비밀번호는웹이나공개저장소에올리지않는다
14. 외부데이터를쓰면출처를표기한다

## 코딩 AI 사용 원칙
위 규칙과 겹치거나 다르면 위 규칙을 따른다.

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

**These guidelines are working if:** fewer unnecessary changes in diffs, fewer rewrites due to overcomplication, and clarifying questions come before implementation rather than after mistakes.
