class RuleBasedMatcher:
    def match(self, students, mentors):
        """基于规则的匹配：简单匹配共同兴趣"""
        matches = {}
        for student_id, student_profile in students.items():
            best_match = None
            best_score = -1
            for mentor_id, mentor_profile in mentors.items():
                # 计算匹配分数：共同兴趣的数量
                common_interests = set(student_profile.get('interests', [])) & set(mentor_profile.get('interests', []))
                score = len(common_interests)
                if score > best_score:
                    best_score = score
                    best_match = mentor_id
            matches[student_id] = best_match
        return matches

    def get_candidates(self, students, mentors):
        """获取候选匹配对"""
        candidates = []
        for student_id, student_profile in students.items():
            for mentor_id, mentor_profile in mentors.items():
                common_interests = set(student_profile.get('interests', [])) & set(mentor_profile.get('interests', []))
                if len(common_interests) > 0:  # 至少有1个共同兴趣才作为候选
                    candidates.append({
                        '学生id': student_id,
                        '导师id': mentor_id,
                        'student_profile': student_profile,
                        'mentor_profile': mentor_profile
                    })
        return candidates


class MLBasedMatcher:
    def recommend_matches(self, students, mentors):
        """基于机器学习的匹配：这里简化为随机推荐"""
        import random
        mentor_ids = list(mentors.keys())
        matches = {}
        for student_id in students.keys():
            matches[student_id] = random.choice(mentor_ids)
        return matches

    def rank_candidates(self, candidates):
        """对候选匹配进行排序：这里简化为随机排序"""
        import random
        random.shuffle(candidates)
        return candidates


def stable_marriage(students, mentors, student_prefs, mentor_prefs):
    """稳定婚姻问题算法实现"""
    if not students or not mentors:
        return {}

    # 初始化所有学生和导师为自由状态
    free_students = list(students)
    free_mentors = list(mentors)

    # 创建偏好字典
    student_pref_dict = {s: {m: i for i, m in enumerate(prefs)}
                         for s, prefs in zip(students, student_prefs)}
    mentor_pref_dict = {m: {s: i for i, s in enumerate(prefs)}
                        for m, prefs in zip(mentors, mentor_prefs)}

    # 当前匹配状态
    matches = {}
    mentor_matches = {m: None for m in mentors}

    while free_students:
        student = free_students[0]
        student_prefs = student_pref_dict[student]

        # 找到学生尚未申请的最高优先级导师
        for mentor in student_prefs:
            if mentor in free_mentors:
                # 直接匹配
                matches[student] = mentor
                mentor_matches[mentor] = student
                free_students.remove(student)
                free_mentors.remove(mentor)
                break
            else:
                # 导师已经被匹配，检查是否更喜欢当前学生
                current_match = mentor_matches[mentor]
                if mentor_pref_dict[mentor][student] < mentor_pref_dict[mentor][current_match]:
                    # 导师更喜欢新学生
                    matches[student] = mentor
                    mentor_matches[mentor] = student
                    free_students.remove(student)
                    free_students.append(current_match)
                    break

    return matches


class MatchingSystem:
    def __init__(self, method='hybrid'):
        self.method = method
        self.students = {}
        self.mentors = {}
        self.historical_matches = []
        self.rule_based_matcher = RuleBasedMatcher()
        self.ml_matcher = MLBasedMatcher()

    def add_student(self, student_id, profile):
        """添加学生信息"""
        self.students[student_id] = {
            'interests': profile.get('interests', []),
            'scores': profile.get('scores', {}),
            'other_info': profile.get('other_info', {})
        }

    def add_mentor(self, mentor_id, profile):
        """添加导师信息"""
        self.mentors[mentor_id] = {
            'interests': profile.get('interests', []),
            'requirements': profile.get('requirements', {}),
            'other_info': profile.get('other_info', {})
        }

    def record_match(self, student_id, mentor_id, success):
        """记录匹配结果"""
        self.historical_matches.append({
            '学生Id': student_id,
            '导师Id': mentor_id,
            'success': success
        })

    def generate_recommendations(self):
        """生成推荐匹配"""
        if self.method == 'rule_based':
            return self.rule_based_matcher.match(self.students, self.mentors)
        elif self.method == 'ml':
            return self.ml_matcher.recommend_matches(self.students, self.mentors)
        else:
            # 混合方法：先用规则筛选，再用ML排序
            candidates = self.rule_based_matcher.get_candidates(self.students, self.mentors)
            ranked_candidates = self.ml_matcher.rank_candidates(candidates)
            # 将列表转换为字典格式以便统一处理
            matches = {}
            for candidate in ranked_candidates:
                student_id = candidate['学生id']
                mentor_id = candidate['导师id']
                if student_id not in matches:  # 只保留每个学生的第一个推荐
                    matches[student_id] = mentor_id
            return matches

    def finalize_matches(self, student_preferences, mentor_preferences):
        """使用稳定婚姻算法进行最终匹配"""
        return stable_marriage(
            list(self.students.keys()),
            list(self.mentors.keys()),
            student_preferences,
            mentor_preferences
        )


def input_profile(role):
    """输入学生或导师的信息"""
    profile = {}
    profile_id = input(f"请输入{role}ID: ")

    # 输入兴趣爱好
    interests = input(f"请输入{role}的兴趣爱好(用逗号分隔): ").split(',')
    profile['interests'] = [i.strip() for i in interests if i.strip()]

    # 输入分数或要求
    scores = {}
    if role == '学生':
        print("请输入学生分数:")
        scores['math'] = float(input("数学分数: "))
        scores['english'] = float(input("英语分数: "))
        scores['programming'] = float(input("编程分数: "))
    else:
        print("请输入导师要求:")
        scores['min_math'] = float(input("最低数学要求: "))
        scores['min_english'] = float(input("最低英语要求: "))
        scores['min_programming'] = float(input("最低编程要求: "))

    profile['scores' if role == '学生' else 'requirements'] = scores

    # 其他信息
    other_info = {}
    other_info['name'] = input(f"{role}姓名: ")
    other_info['age'] = int(input(f"{role}年龄: "))
    if role == '导师':
        other_info['max_students'] = int(input("最多指导学生数: "))

    profile['other_info'] = other_info

    return profile_id, profile


def main():
    system = MatchingSystem(method='hybrid')

    # 添加学生
    num_students = int(input("要添加多少学生? "))
    for _ in range(num_students):
        student_id, profile = input_profile('学生')
        system.add_student(student_id, profile)

    # 添加导师
    num_mentors = int(input("要添加多少导师? "))
    for _ in range(num_mentors):
        mentor_id, profile = input_profile('导师')
        system.add_mentor(mentor_id, profile)

    # 生成推荐
    print("\n生成推荐匹配...")
    recommendations = system.generate_recommendations()
    print("推荐结果:")
    for student, mentor in recommendations.items():
        print(f"学生 {student} -> 导师 {mentor}")

    # 稳定婚姻算法匹配
    print("\n使用稳定婚姻算法进行匹配...")

    # 模拟学生偏好(实际应用中可以从历史数据或用户输入获取)
    student_prefs = []
    for student_id in system.students:
        # 这里简化为按共同兴趣数量排序
        pref = []
        scores = []
        for mentor_id in system.mentors:
            common = len(set(system.students[student_id]['interests']) &
                     set(system.mentors[mentor_id]['interests']))
            scores.append((mentor_id, common))
        # 按共同兴趣数量降序排列
        pref = [m[0] for m in sorted(scores, key=lambda x: x[1], reverse=True)]
        student_prefs.append(pref)

    # 模拟导师偏好(同样简化)
    mentor_prefs = []
    for mentor_id in system.mentors:
        pref = []
        scores = []
        for student_id in system.students:
            # 检查是否满足最低要求
            req = system.mentors[mentor_id]['requirements']
            stu_scores = system.students[student_id]['scores']
            if (stu_scores['math'] >= req['min_math'] and
                    stu_scores['english'] >= req['min_english'] and
                    stu_scores['programming'] >= req['min_programming']):
                common = len(set(system.students[student_id]['interests']) &
                             set(system.mentors[mentor_id]['interests']))
                scores.append((student_id, common))
        # 按共同兴趣数量降序排列
        pref = [s[0] for s in sorted(scores, key=lambda x: x[1], reverse=True)]
        mentor_prefs.append(pref)

    # 进行稳定匹配
    matches = system.finalize_matches(student_prefs, mentor_prefs)
    print("\n最终匹配结果:")
    for student, mentor in matches.items():
        print(f"学生 {student} 匹配到 导师 {mentor}")

        # 显示匹配详情
        stu = system.students[student]
        ment = system.mentors[mentor]
        print(f"  学生兴趣: {', '.join(stu['interests'])}")
        print(f"  导师兴趣: {', '.join(ment['interests'])}")
        print(f"  共同兴趣: {', '.join(set(stu['interests']) & set(ment['interests']))}")
        print()

class RuleBasedMatcher:
    def match(self, students, mentors):
        """基于规则的匹配：简单匹配共同兴趣"""
        matches = {}
        for student_id, student_profile in students.items():
            best_match = None
            best_score = -1
            for mentor_id, mentor_profile in mentors.items():
                # 计算匹配分数：共同兴趣的数量
                common_interests = set(student_profile.get('interests', [])) & set(mentor_profile.get('interests', []))
                score = len(common_interests)
                if score > best_score:
                    best_score = score
                    best_match = mentor_id
            matches[student_id] = best_match
        return matches

    def get_candidates(self, students, mentors):
        """获取候选匹配对"""
        candidates = []
        for student_id, student_profile in students.items():
            for mentor_id, mentor_profile in mentors.items():
                common_interests = set(student_profile.get('interests', [])) & set(mentor_profile.get('interests', []))
                if len(common_interests) > 0:  # 至少有1个共同兴趣才作为候选
                    candidates.append({
                        '学生id': student_id,
                        '导师id': mentor_id,
                        'student_profile': student_profile,
                        'mentor_profile': mentor_profile
                    })
        return candidates


class MLBasedMatcher:
    def recommend_matches(self, students, mentors):
        """基于机器学习的匹配：这里简化为随机推荐"""
        import random
        mentor_ids = list(mentors.keys())
        matches = {}
        for student_id in students.keys():
            matches[student_id] = random.choice(mentor_ids)
        return matches

    def rank_candidates(self, candidates):
        """对候选匹配进行排序：这里简化为随机排序"""
        import random
        random.shuffle(candidates)
        return candidates


def stable_marriage(students, mentors, student_prefs, mentor_prefs):
    """稳定婚姻问题算法实现"""
    if not students or not mentors:
        return {}

    # 初始化所有学生和导师为自由状态
    free_students = list(students)
    free_mentors = list(mentors)

    # 创建偏好字典
    student_pref_dict = {s: {m: i for i, m in enumerate(prefs)}
                         for s, prefs in zip(students, student_prefs)}
    mentor_pref_dict = {m: {s: i for i, s in enumerate(prefs)}
                        for m, prefs in zip(mentors, mentor_prefs)}

    # 当前匹配状态
    matches = {}
    mentor_matches = {m: None for m in mentors}

    while free_students:
        student = free_students[0]
        student_prefs = student_pref_dict[student]

        # 找到学生尚未申请的最高优先级导师
        for mentor in student_prefs:
            if mentor in free_mentors:
                # 直接匹配
                matches[student] = mentor
                mentor_matches[mentor] = student
                free_students.remove(student)
                free_mentors.remove(mentor)
                break
            else:
                # 导师已经被匹配，检查是否更喜欢当前学生
                current_match = mentor_matches[mentor]
                if mentor_pref_dict[mentor][student] < mentor_pref_dict[mentor][current_match]:
                    # 导师更喜欢新学生
                    matches[student] = mentor
                    mentor_matches[mentor] = student
                    free_students.remove(student)
                    free_students.append(current_match)
                    break

    return matches


class MatchingSystem:
    def __init__(self, method='hybrid'):
        self.method = method
        self.students = {}
        self.mentors = {}
        self.historical_matches = []
        self.rule_based_matcher = RuleBasedMatcher()
        self.ml_matcher = MLBasedMatcher()

    def add_student(self, student_id, profile):
        """添加学生信息"""
        self.students[student_id] = {
            'interests': profile.get('interests', []),
            'scores': profile.get('scores', {}),
            'other_info': profile.get('other_info', {})
        }

    def add_mentor(self, mentor_id, profile):
        """添加导师信息"""
        self.mentors[mentor_id] = {
            'interests': profile.get('interests', []),
            'requirements': profile.get('requirements', {}),
            'other_info': profile.get('other_info', {})
        }

    def record_match(self, student_id, mentor_id, success):
        """记录匹配结果"""
        self.historical_matches.append({
            '学生Id': student_id,
            '导师Id': mentor_id,
            'success': success
        })

    def generate_recommendations(self):
        """生成推荐匹配"""
        if self.method == 'rule_based':
            return self.rule_based_matcher.match(self.students, self.mentors)
        elif self.method == 'ml':
            return self.ml_matcher.recommend_matches(self.students, self.mentors)
        else:
            # 混合方法：先用规则筛选，再用ML排序
            candidates = self.rule_based_matcher.get_candidates(self.students, self.mentors)
            ranked_candidates = self.ml_matcher.rank_candidates(candidates)
            # 将列表转换为字典格式以便统一处理
            matches = {}
            for candidate in ranked_candidates:
                student_id = candidate['学生id']
                mentor_id = candidate['导师id']
                if student_id not in matches:  # 只保留每个学生的第一个推荐
                    matches[student_id] = mentor_id
            return matches

    def finalize_matches(self, student_preferences, mentor_preferences):
        """使用稳定婚姻算法进行最终匹配"""
        return stable_marriage(
            list(self.students.keys()),
            list(self.mentors.keys()),
            student_preferences,
            mentor_preferences
        )


def input_profile(role):
    """输入学生或导师的信息"""
    profile = {}
    profile_id = input(f"请输入{role}ID: ")

    # 输入兴趣爱好
    interests = input(f"请输入{role}的兴趣爱好(用逗号分隔): ").split(',')
    profile['interests'] = [i.strip() for i in interests if i.strip()]

    # 输入分数或要求
    scores = {}
    if role == '学生':
        print("请输入学生分数:")
        scores['math'] = float(input("数学分数: "))
        scores['english'] = float(input("英语分数: "))
        scores['programming'] = float(input("编程分数: "))
    else:
        print("请输入导师要求:")
        scores['min_math'] = float(input("最低数学要求: "))
        scores['min_english'] = float(input("最低英语要求: "))
        scores['min_programming'] = float(input("最低编程要求: "))

    profile['scores' if role == '学生' else 'requirements'] = scores

    # 其他信息
    other_info = {}
    other_info['name'] = input(f"{role}姓名: ")
    other_info['age'] = int(input(f"{role}年龄: "))
    if role == '导师':
        other_info['max_students'] = int(input("最多指导学生数: "))

    profile['other_info'] = other_info

    return profile_id, profile


def main():
    system = MatchingSystem(method='hybrid')

    # 添加学生
    num_students = int(input("要添加多少学生? "))
    for _ in range(num_students):
        student_id, profile = input_profile('学生')
        system.add_student(student_id, profile)

    # 添加导师
    num_mentors = int(input("要添加多少导师? "))
    for _ in range(num_mentors):
        mentor_id, profile = input_profile('导师')
        system.add_mentor(mentor_id, profile)

    # 生成推荐
    print("\n生成推荐匹配...")
    recommendations = system.generate_recommendations()
    print("推荐结果:")
    for student, mentor in recommendations.items():
        print(f"学生 {student} -> 导师 {mentor}")

    # 稳定婚姻算法匹配
    print("\n使用稳定婚姻算法进行匹配...")

    # 模拟学生偏好(实际应用中可以从历史数据或用户输入获取)
    student_prefs = []
    for student_id in system.students:
        # 这里简化为按共同兴趣数量排序
        pref = []
        scores = []
        for mentor_id in system.mentors:
            common = len(set(system.students[student_id]['interests']) &
                     set(system.mentors[mentor_id]['interests']))
            scores.append((mentor_id, common))
        # 按共同兴趣数量降序排列
        pref = [m[0] for m in sorted(scores, key=lambda x: x[1], reverse=True)]
        student_prefs.append(pref)

    # 模拟导师偏好(同样简化)
    mentor_prefs = []
    for mentor_id in system.mentors:
        pref = []
        scores = []
        for student_id in system.students:
            # 检查是否满足最低要求
            req = system.mentors[mentor_id]['requirements']
            stu_scores = system.students[student_id]['scores']
            if (stu_scores['math'] >= req['min_math'] and
                    stu_scores['english'] >= req['min_english'] and
                    stu_scores['programming'] >= req['min_programming']):
                common = len(set(system.students[student_id]['interests']) &
                             set(system.mentors[mentor_id]['interests']))
                scores.append((student_id, common))
        # 按共同兴趣数量降序排列
        pref = [s[0] for s in sorted(scores, key=lambda x: x[1], reverse=True)]
        mentor_prefs.append(pref)

    # 进行稳定匹配
    matches = system.finalize_matches(student_prefs, mentor_prefs)
    print("\n最终匹配结果:")
    for student, mentor in matches.items():
        print(f"学生 {student} 匹配到 导师 {mentor}")

        # 显示匹配详情
        stu = system.students[student]
        ment = system.mentors[mentor]
        print(f"  学生兴趣: {', '.join(stu['interests'])}")
        print(f"  导师兴趣: {', '.join(ment['interests'])}")
        print(f"  共同兴趣: {', '.join(set(stu['interests']) & set(ment['interests']))}")
        print()


if __name__ == "__main__":
    main()
