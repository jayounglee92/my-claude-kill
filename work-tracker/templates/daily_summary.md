# {{DATE}}({{DAY}}) 업무 요약

## 근무 시간

{{CLOCKIN}} ~ {{CLOCKOUT}} ({{DURATION}})

## 타임라인

| 시간 | 서비스 | 작업 내용 |
|------|--------|---------|
{{#each timeline}}
| {{start_time}} ~ {{end_time}} | {{service}} | {{description}} |
{{/each}}

## 오늘 한 일

{{#each services}}
### [{{service_name}}] {{repo_name}} ({{start}} ~ {{end}})

{{#each tasks}}
- {{summary}}
{{#each details}}
  - {{time}} | {{description}}
{{/each}}
  - 커밋 {{commit_count}}건{{#if diff}}, {{diff}}{{/if}}
{{#if mr}}
  - {{mr}}
{{/if}}
{{/each}}
{{#if claude_discussion}}
- Claude와 논의한 내용: ({{claude_time}})
{{#each claude_discussion}}
  - {{this}}
{{/each}}
{{/if}}

{{/each}}
{{#if non_code}}
### 코드 외 업무

{{#each non_code}}
- {{time}} | {{description}}
{{/each}}
{{/if}}

## 내일 할 일 / 미해결

{{#each todos}}
- {{this}}
{{/each}}
