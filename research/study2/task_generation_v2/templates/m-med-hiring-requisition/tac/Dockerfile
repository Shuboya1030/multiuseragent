FROM tac-study21-ungraded-base:v1
ARG PROFILE=R1
COPY task.md /instruction/task.md
COPY scenarios.json /npc/scenarios.json
COPY dependencies.yml /utils/dependencies.yml
COPY populate_data.py /utils/populate_data.py
COPY documents_${PROFILE}/ /utils/task_documents/
WORKDIR /workspace
