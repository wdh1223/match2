import streamlit as st
from datetime import datetime, date, time
import pandas as pd
import numpy as np
from collections import defaultdict
import hashlib


# 密码验证函数 - 简化版本
def simple_password_check():
    """简单的密码验证"""
    # 默认密码
    DEFAULT_PASSWORD = "123321456"

    # 初始化会话状态
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
        st.session_state.password_attempt = False

    if not st.session_state.authenticated:
        password = st.text_input("请输入系统访问密码:", type="password", key="login_password")
        if st.button("登录", key="login_btn"):
            if password == DEFAULT_PASSWORD:
                st.session_state.authenticated = True
                st.session_state.password_attempt = False
                st.rerun()
            else:
                st.session_state.password_attempt = True
                st.error("密码不正确，请重试")
        return st.session_state.authenticated
    return True


class MatchingSystem:
    def __init__(self, method='hybrid'):
        self.students = {}
        self.mentors = {}
        self.method = method

    def add_student(self, student_id, profile):
        self.students[student_id] = profile

    def add_mentor(self, mentor_id, profile):
        self.mentors[mentor_id] = profile

    def finalize_matches(self, student_ids, mentor_ids, student_prefs, mentor_prefs):
        """执行稳定匹配算法"""
        # 实现Gale-Shapley稳定匹配算法
        matches = {}  # 存储最终匹配结果 {学生: 导师}
        mentor_matches = defaultdict(list)  # 导师匹配的学生列表

        # 创建导师偏好索引映射
        mentor_pref_rankings = {}
        for i, mentor_id in enumerate(mentor_ids):
            mentor_pref_rankings[mentor_id] = {}
            for rank, student_id in enumerate(mentor_prefs[i]):
                mentor_pref_rankings[mentor_id][student_id] = rank

        # 初始化每个学生的提案索引
        student_proposal_index = {student_id: 0 for student_id in student_ids}

        # 获取导师最多能带的学生数
        mentor_capacities = {
            mentor_id: self.mentors[mentor_id]['other_info']['max_students']
            for mentor_id in mentor_ids
        }

        # 还有学生没有匹配且还有可选的导师
        free_students = list(student_ids)
        while free_students:
            student_id = free_students.pop(0)

            # 如果学生已经尝试了所有导师，跳过
            if student_proposal_index[student_id] >= len(student_prefs[student_ids.index(student_id)]):
                continue

            # 获取学生下一个想申请的导师
            mentor_id = student_prefs[student_ids.index(student_id)][student_proposal_index[student_id]]
            student_proposal_index[student_id] += 1

            # 如果导师还有名额，直接匹配
            if len(mentor_matches[mentor_id]) < mentor_capacities[mentor_id]:
                matches[student_id] = mentor_id
                mentor_matches[mentor_id].append(student_id)
            else:
                # 检查当前学生是否比已匹配的某个学生更受导师青睐
                current_matches = mentor_matches[mentor_id]
                for matched_student in current_matches:
                    # 如果新学生比已匹配学生排名更高
                    if mentor_pref_rankings[mentor_id].get(student_id, float('inf')) < \
                            mentor_pref_rankings[mentor_id].get(matched_student, float('inf')):
                        # 替换匹配
                        del matches[matched_student]
                        mentor_matches[mentor_id].remove(matched_student)
                        matches[student_id] = mentor_id
                        mentor_matches[mentor_id].append(student_id)
                        free_students.append(matched_student)
                        break
                else:
                    # 如果没有替换发生，学生继续保持自由
                    free_students.append(student_id)

        return matches


def input_project_info():
    """输入项目基本信息"""
    st.subheader("项目基本信息")

    col1, col2 = st.columns(2)
    with col1:
        project_name = st.text_input("项目名称", "2024春季机器学习项目", key="project_name")
        project_manager = st.text_input("项目负责人", "张老师", key="project_manager")
    with col2:
        project_duration = st.selectbox("项目周期", ["1个月", "2个月", "3个月", "半年", "全年"], key="project_duration")
        max_participants = st.number_input("最大参与人数", min_value=5, max_value=100, value=20, key="max_participants")

    st.subheader("项目时间段")
    col_date1, col_date2 = st.columns(2)
    with col_date1:
        project_start = st.date_input("项目开始日期", date(2024, 3, 1), key="project_start")
    with col_date2:
        project_end = st.date_input("项目结束日期", date(2024, 6, 30), key="project_end")

    st.subheader("每周活动时间")
    col_time1, col_time2 = st.columns(2)
    with col_time1:
        weekly_start = st.time_input("每周开始时间", time(14, 0), key="weekly_start")
    with col_time2:
        weekly_end = st.time_input("每周结束时间", time(17, 0), key="weekly_end")

    # 选择活动日
    week_days = st.multiselect(
        "选择活动日",
        ["周一", "周二", "周三", "周四", "周五", "周六", "周日"],
        default=["周二", "周四"],
        key="week_days"
    )

    project_info = {
        'name': project_name,
        'manager': project_manager,
        'duration': project_duration,
        'max_participants': max_participants,
        'start_date': project_start,
        'end_date': project_end,
        'weekly_start_time': weekly_start,
        'weekly_end_time': weekly_end,
        'activity_days': week_days
    }

    return project_info


def input_student_profile(student_idx, project_info):
    """输入单个学生信息"""
    st.subheader(f"学生 {student_idx + 1} 信息")

    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input(f"学号 {student_idx + 1}", key=f"stu_id_{student_idx}")
        name = st.text_input(f"姓名 {student_idx + 1}", key=f"stu_name_{student_idx}")
        grade = st.selectbox(f"年级 {student_idx + 1}", ["大一", "大二", "大三", "大四", "研究生"],
                             key=f"stu_grade_{student_idx}")

    with col2:
        major = st.text_input(f"专业 {student_idx + 1}", key=f"stu_major_{student_idx}")
        email = st.text_input(f"邮箱 {student_idx + 1}", key=f"stu_email_{student_idx}")
        phone = st.text_input(f"电话 {student_idx + 1}", key=f"stu_phone_{student_idx}")

    # 兴趣爱好和技能
    interests = st.text_area(
        f"兴趣爱好（用逗号分隔） {student_idx + 1}",
        "机器学习,人工智能,数据分析,编程",
        key=f"stu_interests_{student_idx}"
    )

    # 技能水平自评
    st.write("技能水平自评（1-5分，5分为最高）:")
    col_skill1, col_skill2, col_skill3 = st.columns(3)
    with col_skill1:
        math_skill = st.slider("数学能力", 1, 5, 3, key=f"stu_math_{student_idx}")
    with col_skill2:
        programming_skill = st.slider("编程能力", 1, 5, 3, key=f"stu_programming_{student_idx}")
    with col_skill3:
        english_skill = st.slider("英语能力", 1, 5, 3, key=f"stu_english_{student_idx}")

    # 可用时间确认
    st.write("请确认你的可用时间与项目时间是否一致:")
    time_match = st.checkbox(
        f"我的可用时间与项目时间一致（{project_info['activity_days']} {project_info['weekly_start_time']}-{project_info['weekly_end_time']}）",
        value=True,
        key=f"stu_time_match_{student_idx}"
    )

    if not time_match:
        st.warning("如果你的可用时间与项目时间不一致，可能会影响匹配结果")

    # 验证必填项
    if not student_id or not name or not interests:
        st.warning(f"学生 {student_idx + 1} 的学号、姓名和兴趣为必填项！")
        return None, None

    # 整理为profile格式
    profile = {
        'interests': [i.strip() for i in interests.split(',') if i.strip()],
        'skills': {
            'math': math_skill,
            'programming': programming_skill,
            'english': english_skill
        },
        'availability': {
            'matches_project': time_match,
            'project_days': project_info['activity_days'],
            'project_start_time': project_info['weekly_start_time'],
            'project_end_time': project_info['weekly_end_time']
        },
        'other_info': {
            'name': name,
            'grade': grade,
            'major': major,
            'email': email,
            'phone': phone,
            'project': project_info['name']
        }
    }
    return student_id, profile


def input_mentor_profile(mentor_idx, project_info):
    """输入单个导师信息"""
    st.subheader(f"导师 {mentor_idx + 1} 信息")

    col1, col2 = st.columns(2)
    with col1:
        mentor_id = st.text_input(f"工号 {mentor_idx + 1}", key=f"ment_id_{mentor_idx}")
        name = st.text_input(f"姓名 {mentor_idx + 1}", key=f"ment_name_{mentor_idx}")
        title = st.selectbox(
            f"职称 {mentor_idx + 1}",
            ["讲师", "助理教授", "副教授", "教授", "研究员", "高级工程师"],
            key=f"ment_title_{mentor_idx}"
        )

    with col2:
        department = st.text_input(f"院系 {mentor_idx + 1}", key=f"ment_department_{mentor_idx}")
        email = st.text_input(f"邮箱 {mentor_idx + 1}", key=f"ment_email_{mentor_idx}")
        phone = st.text_input(f"电话 {mentor_idx + 1}", key=f"ment_phone_{mentor_idx}")

    # 研究领域和指导方向
    research_areas = st.text_area(
        f"研究领域（用逗号分隔） {mentor_idx + 1}",
        "机器学习,人工智能,数据挖掘,自然语言处理",
        key=f"ment_research_{mentor_idx}"
    )

    max_students = st.slider(f"最多指导学生数 {mentor_idx + 1}", 1, 10, 3, key=f"ment_max_{mentor_idx}")

    # 技能要求
    st.write("对学生的最低技能要求（1-5分，5分为最高）:")
    col_req1, col_req2, col_req3 = st.columns(3)
    with col_req1:
        min_math = st.slider("数学要求", 1, 5, 2, key=f"ment_min_math_{mentor_idx}")
    with col_req2:
        min_programming = st.slider("编程要求", 1, 5, 3, key=f"ment_min_programming_{mentor_idx}")
    with col_req3:
        min_english = st.slider("英语要求", 1, 5, 2, key=f"ment_min_english_{mentor_idx}")

    # 可用时间确认
    st.write("请确认你的可用时间与项目时间是否一致:")
    time_match = st.checkbox(
        f"我的可用时间与项目时间一致（{project_info['activity_days']} {project_info['weekly_start_time']}-{project_info['weekly_end_time']}）",
        value=True,
        key=f"ment_time_match_{mentor_idx}"
    )

    if not time_match:
        st.warning("如果你的可用时间与项目时间不一致，可能会影响匹配结果")

    # 验证必填项
    if not mentor_id or not name or not research_areas:
        st.warning(f"导师 {mentor_idx + 1} 的工号、姓名和研究领域为必填项！")
        return None, None

    # 整理为profile格式
    profile = {
        'research_areas': [i.strip() for i in research_areas.split(',') if i.strip()],
        'requirements': {
            'min_math': min_math,
            'min_programming': min_programming,
            'min_english': min_english
        },
        'availability': {
            'matches_project': time_match,
            'project_days': project_info['activity_days'],
            'project_start_time': project_info['weekly_start_time'],
            'project_end_time': project_info['weekly_end_time']
        },
        'other_info': {
            'name': name,
            'title': title,
            'department': department,
            'email': email,
            'phone': phone,
            'max_students': max_students,
            'project': project_info['name']
        }
    }
    return mentor_id, profile


def check_time_compatibility(student_avail, mentor_avail):
    """检查学生和导师的时间兼容性"""
    # 如果双方都确认时间与项目匹配，则时间兼容
    if student_avail['matches_project'] and mentor_avail['matches_project']:
        return True

    # 这里可以添加更复杂的时间匹配逻辑
    # 例如比较具体的时间段等

    return False


def main():
    st.title("项目制学生导师匹配系统")

    # 检查密码
    if not simple_password_check():
        st.stop()

    # 显示系统内容
    st.success("✅ 已成功登录系统")

    # 初始化session_state保存状态
    if 'system' not in st.session_state:
        st.session_state.system = MatchingSystem(method='hybrid')
    if 'current_project' not in st.session_state:
        st.session_state.current_project = None
    if 'students_added' not in st.session_state:
        st.session_state.students_added = 0
    if 'mentors_added' not in st.session_state:
        st.session_state.mentors_added = 0

    system = st.session_state.system

    # 步骤1：创建项目
    st.header("1. 创建项目")
    project_info = input_project_info()

    if st.button("创建项目", key="create_project_btn"):
        st.session_state.current_project = project_info
        st.session_state.students_added = 0
        st.session_state.mentors_added = 0
        st.success(f"项目 '{project_info['name']}' 创建成功！")

    # 显示当前项目信息
    if st.session_state.current_project:
        st.info(f"当前项目: {st.session_state.current_project['name']} | "
                f"负责人: {st.session_state.current_project['manager']} | "
                f"周期: {st.session_state.current_project['duration']} | "
                f"活动时间: {st.session_state.current_project['activity_days']} "
                f"{st.session_state.current_project['weekly_start_time']}-"
                f"{st.session_state.current_project['weekly_end_time']}")

    # 步骤2：添加学生
    st.header("2. 添加学生")
    if st.session_state.current_project:
        num_students = st.number_input(
            "要添加的学生数量",
            min_value=0,
            max_value=st.session_state.current_project['max_participants'],
            value=0,
            key="num_stu"
        )

        if num_students > 0:
            for i in range(num_students):
                student_id, profile = input_student_profile(i, st.session_state.current_project)
                if student_id and profile:  # 仅当输入有效时添加
                    # 添加项目信息到学生ID
                    student_id_with_project = f"{st.session_state.current_project['name']}_{student_id}"
                    system.add_student(student_id_with_project, profile)
                    st.session_state.students_added += 1
            st.success(f"已为项目添加 {num_students} 名学生！当前共 {st.session_state.students_added} 名学生")
    else:
        st.warning("请先创建项目")

    # 步骤3：添加导师
    st.header("3. 添加导师")
    if st.session_state.current_project:
        num_mentors = st.number_input(
            "要添加的导师数量",
            min_value=0,
            max_value=10,
            value=0,
            key="num_ment"
        )

        if num_mentors > 0:
            for i in range(num_mentors):
                mentor_id, profile = input_mentor_profile(i, st.session_state.current_project)
                if mentor_id and profile:  # 仅当输入有效时添加
                    # 添加项目信息到导师ID
                    mentor_id_with_project = f"{st.session_state.current_project['name']}_{mentor_id}"
                    system.add_mentor(mentor_id_with_project, profile)
                    st.session_state.mentors_added += 1
            st.success(f"已为项目添加 {num_mentors} 名导师！当前共 {st.session_state.mentors_added} 名导师")
    else:
        st.warning("请先创建项目")

    # 步骤4：生成匹配结果
    st.header("4. 匹配结果")
    if st.session_state.current_project and st.session_state.students_added > 0 and st.session_state.mentors_added > 0:
        if st.button("生成匹配结果", key="match_btn"):
            # 获取当前项目的学生和导师
            project_name = st.session_state.current_project['name']
            project_students = {sid: profile for sid, profile in system.students.items()
                                if profile['other_info']['project'] == project_name}
            project_mentors = {mid: profile for mid, profile in system.mentors.items()
                               if profile['other_info']['project'] == project_name}

            # 生成学生偏好（考虑时间兼容性和兴趣匹配）
            student_prefs = []
            student_ids = list(project_students.keys())

            for student_id in student_ids:
                scores = []
                student_profile = project_students[student_id]

                for mentor_id in project_mentors:
                    mentor_profile = project_mentors[mentor_id]

                    # 检查时间兼容性
                    time_compatible = check_time_compatibility(
                        student_profile['availability'],
                        mentor_profile['availability']
                    )

                    if time_compatible:
                        # 计算兴趣匹配度
                        common = len(set(student_profile['interests']) &
                                     set(mentor_profile['research_areas']))
                        scores.append((mentor_id, common))
                    else:
                        # 时间不兼容，分数为0
                        scores.append((mentor_id, 0))

                # 按匹配度降序排序
                pref = [m[0] for m in sorted(scores, key=lambda x: x[1], reverse=True) if m[1] > 0]
                student_prefs.append(pref)

            # 生成导师偏好（考虑时间兼容性和技能要求）
            mentor_prefs = []
            mentor_ids = list(project_mentors.keys())

            for mentor_id in mentor_ids:
                scores = []
                mentor_profile = project_mentors[mentor_id]
                req = mentor_profile['requirements']

                for student_id in student_ids:
                    student_profile = project_students[student_id]

                    # 检查时间兼容性
                    time_compatible = check_time_compatibility(
                        student_profile['availability'],
                        mentor_profile['availability']
                    )

                    if time_compatible:
                        stu_skills = student_profile['skills']
                        # 检查是否满足最低要求
                        if (stu_skills['math'] >= req['min_math'] and
                                stu_skills['programming'] >= req['min_programming'] and
                                stu_skills['english'] >= req['min_english']):
                            # 计算兴趣匹配度
                            common = len(set(student_profile['interests']) &
                                         set(mentor_profile['research_areas']))
                            scores.append((student_id, common))

                # 按匹配度降序排序
                pref = [s[0] for s in sorted(scores, key=lambda x: x[1], reverse=True)]
                mentor_prefs.append(pref)

            # 执行稳定匹配
            matches = system.finalize_matches(
                student_ids,
                mentor_ids,
                student_prefs,
                mentor_prefs
            )

            # 显示匹配结果
            st.subheader(f"项目 '{project_name}' 匹配结果")

            if not matches:
                st.warning("未能找到有效的匹配！请检查时间兼容性或放宽要求。")
            else:
                # 统计匹配结果
                mentor_counts = {}
                for mentor in mentor_ids:
                    mentor_counts[mentor] = 0

                for student, mentor in matches.items():
                    mentor_counts[mentor] += 1

                # 显示匹配详情
                for mentor_id, count in mentor_counts.items():
                    if count > 0:
                        mentor_profile = project_mentors[mentor_id]
                        raw_mentor_id = mentor_id.split('_', 1)[1] if '_' in mentor_id else mentor_id

                        st.write(f"### 导师 {raw_mentor_id} ({mentor_profile['other_info']['name']})")
                        st.write(f"**指导人数**: {count}/{mentor_profile['other_info']['max_students']}")
                        st.write(f"**研究领域**: {', '.join(mentor_profile['research_areas'])}")

                        # 显示匹配的学生
                        matched_students = [s for s, m in matches.items() if m == mentor_id]
                        for student_id in matched_students:
                            student_profile = project_students[student_id]
                            raw_student_id = student_id.split('_', 1)[1] if '_' in student_id else student_id

                            st.write(f"- **学生 {raw_student_id}** ({student_profile['other_info']['name']})")
                            st.write(f"  兴趣: {', '.join(student_profile['interests'])}")

                            common = set(student_profile['interests']) & set(mentor_profile['research_areas'])
                            st.write(f"  共同领域: {', '.join(common) if common else '无'}")

                        st.divider()

                # 显示未匹配的学生
                unmatched_students = set(student_ids) - set(matches.keys())
                if unmatched_students:
                    st.warning("以下学生未能匹配到导师:")
                    for student_id in unmatched_students:
                        student_profile = project_students[student_id]
                        raw_student_id = student_id.split('_', 1)[1] if '_' in student_id else student_id
                        st.write(f"- {raw_student_id} ({student_profile['other_info']['name']})")
    else:
        st.warning("请先创建项目并添加学生和导师信息")

    # 添加退出登录按钮
    if st.sidebar.button("退出登录"):
        st.session_state.authenticated = False
        st.session_state.current_project = None
        st.session_state.students_added = 0
        st.session_state.mentors_added = 0
        st.session_state.system = MatchingSystem(method='hybrid')
        st.rerun()


if __name__ == "__main__":
    main()