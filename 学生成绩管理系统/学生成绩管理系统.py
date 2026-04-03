import pymysql
import subprocess

# 连接数据库获取用户权限
def user_login(username, ID):
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        user_power = 0  # 默认权限等级
        cursor = conn.cursor()  # 获取游标

        # 验证登录
        cursor.execute("SELECT * FROM School")  # 执行sql
        for row in cursor.fetchall():
            if username == row[1] and ID == row[0]:
                user_power = row[2]
                break

        cursor.execute("SELECT * FROM Teachers")  # 执行sql
        for row in cursor.fetchall():
            if user_power != 0:
                break
            if username == row[1] and ID == row[0]:
                user_power = row[2]
                break

        cursor.execute("SELECT * FROM Students")  # 执行sql
        for row in cursor.fetchall():
            if user_power != 0:
                break
            if username == row[1] and ID == row[0]:
                user_power = row[2]
                break

    except pymysql.Error as e:
        print("Error: 无法连接数据库！", e)
    finally:
        conn.close()  # 关闭数据库连接
        return user_power

#-------------------------------------学生功能函数部分----------------------------------------#
#选课
def choice_course(ID):
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute(f"SELECT ArrangementID, CourseID, TeacherID, StartTime, EndTime FROM CourseArrangements WHERE StartTime <= {today} AND EndTime >= {today}")  # 执行sql
        # 获取所有可选的课程安排
        available_arrangements = cursor.fetchall()
        if not available_arrangements:
            print("当前日期不在任何课程的选课时间内。")
            return
        print("选课ID 课程ID 教师ID")
        for row in available_arrangements:
            print(row[0],row[1],row[2])
        choice = int(input("选择课程ID："))
        if any(arr[0] == choice for arr in available_arrangements):
            cursor.execute(f'INSERT INTO Enrollments(StudentID,ArrangementID) VALUES ({ID}, {choice})')
            conn.commit()  # 提交事务，否则无法在数据库修改
            print("选课成功！")
        else:
            print("选择的课程ID不在可选课程列表中。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#退课
def back_course(ID):
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute(f'SELECT ca.ArrangementID, ca.CourseID, ca.TeacherID, ca.StartTime, ca.EndTime FROM CourseArrangements ca JOIN Enrollments e ON ca.ArrangementID = e.ArrangementID WHERE e.StudentID = {ID}')  # 执行sql
        # 获取所有可退选的课程安排
        available_arrangements = cursor.fetchall()
        if not available_arrangements:
            print("当前日期不在任何课程的退课时间内。")
            return
        print('已选的课程：\n选课ID 课程ID 教师ID')
        for row in available_arrangements:
            print(row[0],row[1],row[2])
        choice = int(input("选择退课的课程ID："))
        if any(arr[0] == choice for arr in available_arrangements):
            cursor.execute(f'DELETE FROM Enrollments WHERE ArrangementID = {choice} AND StudentID = {ID}')
            conn.commit()
            print("退课成功！")
        else:
            print("退选的课程ID不在退选课程列表中。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#查询单科成绩
def secletone(ID):
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute(f'SELECT  ca.ArrangementID,ca.CourseID, ca.TeacherID FROM CourseArrangements ca JOIN Enrollments e ON ca.ArrangementID = e.ArrangementID WHERE e.StudentID = {ID}')
        print('已选的课程：\n选课ID 课程ID 教师ID')
        for row in cursor.fetchall():
            print(row)
        choice = int(input("选择查询成绩的选课ID："))
        cursor.execute(f'SELECT e.ArrangementID, e.Score FROM Enrollments e JOIN CourseArrangements ca ON ca.ArrangementID = e.ArrangementID WHERE e.StudentID = {ID} AND ca.ArrangementID = {choice}')
        print('选课ID  成绩:')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#查询全部成绩和学籍分
def secletall(ID):
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute(f'SELECT ca.ArrangementID, ca.CourseID, ca.TeacherID, e.Score FROM CourseArrangements ca JOIN Enrollments e ON ca.ArrangementID = e.ArrangementID WHERE e.StudentID = {ID}')
        print('选课ID 课程ID 教师ID 成绩:')
        for row in cursor.fetchall():
            print(row)
        cursor.execute(f'SELECT Endscore FROM Students WHERE StudentID = {ID}')
        print('学籍分：')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

# #查询平均学绩分
# def secletGPA(ID):
#     try:
#         # 连接到数据库
#         conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
#         cursor = conn.cursor()  # 获取游标
#         cursor.execute(f'SELECT GPA FROM Students WHERE StudentID = {ID}')
#         print('平均学绩分:')
#         for row in cursor.fetchall():
#             print(row)
#     except pymysql.Error as e:
#         print(f"发生错误：{e}")
#         conn.rollback()  # 发生错误时回滚事务
#     finally:
#         conn.close()  # 关闭数据库连接


#-------------------------------------学生功能函数部分----------------------------------------#

#-------------------------------------教师功能函数部分----------------------------------------#
#教师评分
def givescore(ID):
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute(f'SELECT e.StudentID, e.ArrangementID, ca.InTime FROM Enrollments e JOIN CourseArrangements ca ON e.ArrangementID = ca.ArrangementID WHERE ca.TeacherID = {ID} AND {today} <= ca.InTime')
        #获取截至评分时间
        available_arrangements = cursor.fetchall()
        if not available_arrangements:
            print("没有学生需要评分/不在评分时间内。")
            return
        print('学生ID 选课ID:')
        for row in available_arrangements:
            print(row[0],row[1])
            score = int(input('请评写成绩:'))
            cursor.execute(f'UPDATE Enrollments SET Score = {score} WHERE StudentID = {row[0]} AND ArrangementID = {row[1]}')
            conn.commit()
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#查询课程教学班成绩表
def scletCA():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute('SELECT ArrangementID, CourseID, TeacherID FROM CourseArrangements')
        print("选课班级ID 课程ID 教师ID")
        for row in cursor.fetchall():
            print(row)
        id = int(input('请输入查询的课程教学班ID\n'))
        cursor.execute(f'SELECT s.StudentID,s.Name,c.CourseID,c.TeacherID,e.Score FROM Students s JOIN  Enrollments e ON s.StudentID = e.StudentID JOIN CourseArrangements c ON e.ArrangementID = c.ArrangementID WHERE c.ArrangementID = {id}')
        print('学生ID 学生姓名 课程ID 教师ID 成绩:')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#查询班级成绩表
def secletclass():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute('SELECT ClassID, ClassName FROM Classes')
        print("班级ID 班级名字")
        for row in cursor.fetchall():
            print(row)
        id = int(input('请选择查询的选课班级:'))
        cursor.execute(f'SELECT s.StudentID,s.Name,c.CourseID,c.TeacherID,e.Score FROM Students s JOIN  Enrollments e ON s.StudentID = e.StudentID JOIN CourseArrangements c ON e.ArrangementID = c.ArrangementID WHERE s.ClassID = {id}')
        print('学生ID 学生姓名 课程ID 教师ID 成绩:')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#统计选课班级数据
def Statisticsclass():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute('SELECT ArrangementID, CourseID, TeacherID FROM CourseArrangements')
        print("选课班级ID 课程ID 教师ID")
        for row in cursor.fetchall():
            print(row)
        id = int(input('请选择查询的选课班级:'))
        cursor.execute(f'SELECT AVG(Score) AS AverageScore, MAX(Score) AS MaxScore, MIN(Score) AS MinScore, (SUM(CASE WHEN Score >= 60 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PassRate FROM Enrollments WHERE ArrangementID = {id}')
        print('平均成绩 最高成绩 最低成绩 及格率:')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#统计课程数据
def Statisticsca():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute('SELECT CourseID, CourseName FROM Courses')
        print("课程ID 课程名称")
        for row in cursor.fetchall():
            print(row)
        id = int(input('请选择查询的课程ID:'))
        cursor.execute(f'SELECT AVG(e.Score) AS AverageScore, MAX(e.Score) AS MaxScore, MIN(e.Score) AS MinScore, (SUM(CASE WHEN e.Score >= 60 THEN 1 ELSE 0 END) / COUNT(*)) * 100 AS PassRate FROM Enrollments e JOIN CourseArrangements ca ON e.ArrangementID = ca.ArrangementID WHERE ca.CourseID = {id}')
        print('平均成绩 最高成绩 最低成绩 及格率:')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#统计学生的平均成绩
def Statisticscouse():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute('SELECT StudentID, Name FROM Students')
        print('学生ID 学生姓名')
        for row in cursor.fetchall():
            print(row)
        id = int(input('请输入查询的学生ID:'))
        cursor.execute(f'SELECT AVG(Score) AS AverageScore FROM Enrollments WHERE StudentID ={id}')
        print('平均成绩为:')
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#输出学生名单
def givestu():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        cursor.execute('SELECT ClassID, ClassName FROM Classes')
        print("班级ID 班级名字")
        for row in cursor.fetchall():
            print(row)
        id = int(input('请选择查询的选课班级:'))
        # 调用存储过程并获取结果
        cursor.execute(f'CALL GetStudentsByClass({id})')
        # 获取存储过程返回的结果集
        print("学生ID 学生姓名 学籍分")
        for row in cursor.fetchall():
            print(row)
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接
#-------------------------------------教师功能函数部分----------------------------------------#

#-------------------------------------教务功能函数部分----------------------------------------#
#学生表操作
def sturoot():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        while True:
            choice = input('请选择操作:\n1.查询学生表\n2.添加学生\n3.删除学生\n4.退出系统\n')
            if choice == '1':
                cursor.execute('SELECT * FROM StudentInfo')
                print('学生ID 学生姓名 学生班级ID')
                for row in cursor.fetchall():
                    print(row)
            elif choice == '2':
                stuid = int(input('请添加学生ID:'))
                stuname = input('请添加学生姓名:')
                stuclass = int(input('请添加学生班级ID:'))
                cursor.execute(f'INSERT INTO Students (StudentID, Name, ClassID) VALUES ({stuid},"{stuname}",{stuclass})')
                conn.commit()
            elif choice == '3':
                stuid = int(input('请输入删除的学生ID:'))
                cursor.execute(f'DELETE FROM Students WHERE StudentID = {stuid}')
                conn.commit()
            elif choice == '4':
                break  # 退出函数
            else:
                print("无效选项，请重新选择。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#教师表操作
def teacherroot():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        while True:
            choice = input('请选择操作:\n1.查询教师表\n2.添加教师\n3.删除教师\n4.退出系统\n')
            if choice == '1':
                cursor.execute('SELECT TeacherID, Name FROM Teachers')
                print('教师ID 教师姓名 ')
                for row in cursor.fetchall():
                    print(row)
            elif choice == '2':
                teacherid = int(input('请添加教师ID:'))
                teachername = input('请添加教师姓名:')
                cursor.execute(f'INSERT INTO Teachers (TeacherID, Name) VALUES ({teacherid},"{teachername}")')
                conn.commit()
            elif choice == '3':
                teacherid = int(input('请输入删除的教师ID:'))
                cursor.execute(f'DELETE FROM Teachers WHERE TeacherID = {teacherid}')
                conn.commit()
            elif choice == '4':
                break  # 退出函数
            else:
                print("无效选项，请重新选择。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#班级表操作
def classroot():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        while True:
            choice = input('请选择操作:\n1.查询班级表\n2.添加班级\n3.删除班级\n4.退出系统\n')
            if choice == '1':
                cursor.execute('SELECT * FROM Classes')
                print('班级ID 班级名称 ')
                for row in cursor.fetchall():
                    print(row)
            elif choice == '2':
                Classid = int(input('请添加班级ID:'))
                classname = input('请添加班级名称:')
                cursor.execute(f'INSERT INTO Classes (ClassID, ClassName) VALUES ({Classid},"{classname}")')
                conn.commit()
            elif choice == '3':
                classid = int(input('请输入删除的班级ID:'))
                cursor.execute(f'DELETE FROM Classes WHERE ClassID = {classid}')
                conn.commit()
            elif choice == '4':
                break  # 退出函数
            else:
                print("无效选项，请重新选择。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#课程表操作
def courseroot():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        while True:
            choice = input('请选择操作:\n1.查询课程表\n2.添加课程\n3.删除课程\n4.退出系统\n')
            if choice == '1':
                cursor.execute('SELECT CourseID, CourseName FROM Courses')
                print('课程ID 课程名称 ')
                for row in cursor.fetchall():
                    print(row)
            elif choice == '2':
                courseid = int(input('请添加课程ID:'))
                coursename = input('请添加课程名称:')
                credit = int(input('请添加课程学分:'))
                cursor.execute(f'INSERT INTO Courses (CourseID, CourseName, Credit) VALUES ({courseid},"{coursename}",{credit})')
                conn.commit()
            elif choice == '3':
                courseid = int(input('请输入删除的课程ID:'))
                cursor.execute(f'DELETE FROM Courses WHERE CourseID = {courseid}')
                conn.commit()
            elif choice == '4':
                break  # 退出函数
            else:
                print("无效选项，请重新选择。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

#选课表操作
def Arrangeroot():
    try:
        # 连接到数据库
        conn = pymysql.connect(host='localhost', user='root', password='lyc672987', db='end')
        cursor = conn.cursor()  # 获取游标
        while True:
            choice = input('请选择操作:\n1.查询选课表\n2.添加选课\n3.删除选课\n4.退出系统\n')
            if choice == '1':
                cursor.execute('SELECT ArrangementID, CourseID, TeacherID FROM CourseArrangements')
                print('选课ID 课程ID 教师ID ')
                for row in cursor.fetchall():
                    print(row)
            elif choice == '2':
                Arrangeid = int(input('请添加选课ID:'))
                courseid = int(input('请添加课程ID:'))
                teacherid = int(input('请添加教师ID:'))
                starttime = int(input('请添加选课开始时间:'))
                endtime = int(input('请添加选课结束时间:'))
                intime = int(input('请添加评分截止时间:'))
                studentlimit = int(input('请添加限选人数:'))
                cursor.execute(f'INSERT INTO CourseArrangements (ArrangementID, CourseID, TeacherID, StartTime, EndTime, InTime, StudentLimit) VALUES ({Arrangeid},{courseid},{teacherid},{starttime},{endtime},{intime},{studentlimit})')
                conn.commit()
            elif choice == '3':
                Arrangeid = int(input('请输入删除的选课ID:'))
                cursor.execute(f'DELETE FROM CourseArrangements WHERE ArrangementID = {Arrangeid}')
                conn.commit()
            elif choice == '4':
                break  # 退出函数
            else:
                print("无效选项，请重新选择。")
    except pymysql.Error as e:
        print(f"发生错误：{e}")
        conn.rollback()  # 发生错误时回滚事务
    finally:
        conn.close()  # 关闭数据库连接

# 备份数据库
def backup_database(host, user, password, database, output_file):
    try:
        command = f"mysqldump -h {host} -u {user} -p{password} {database} > {output_file}"
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("数据库备份成功！")
    except Exception as e:
        print("Error backing up database:", e)

# 恢复数据库
def restore_database(host, user, password, database, input_file):
    try:
        command = f"mysql -h {host} -u {user} -p{password} {database} < {input_file}"
        subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("数据库恢复成功！")
    except Exception as e:
        print("Error restoring database:", e)

# 设置数据库连接信息和备份/恢复文件路径
host = 'localhost'
user = 'root'
password = 'lyc672987'
database = 'end'
backup_file = r"C:\Users\lyc26\Desktop\end.sql"


#-------------------------------------教务功能函数部分----------------------------------------#


# 主程序流程
today = int(input("今天日期是（20001230）："))
username = input("请输入用户名：")
ID = int(input("请输入ID："))
user_power = user_login(username, ID)

if user_power == 0:
    print("登录失败！")

elif user_power == 1:
    print("学生登录成功！")
    while True:
        choice = input("请选择操作：\n1. 选课\n2. 退课\n3. 查询成绩\n4. 退出系统\n")
        if choice == '1':
            choice_course(ID)
        elif choice == '2':
            back_course(ID)
        elif choice == '3':
            choice2 = input('请选择操作：\n1.查询单科成绩\n2.查询全部成绩和学籍分\n') #3.查询平均学分绩点GPA\n
            if choice2 == '1':
                secletone(ID)
            elif choice2 == '2':
                secletall(ID)
            # elif choice2 == '3':
            #     secletGPA(ID)
            else:
                print("无效选项，请重新选择。")
        elif choice == '4':
            break  # 退出系统
        else:
            print("无效选项，请重新选择。")

elif user_power == 2:
    print("教师登录成功！")
    while True:
        choice = input("请选择操作：\n1. 评分\n2. 查询课程教学班成绩表\n3. 查询班级成绩表\n4. 按班级统计数据\n5. 按课程统计数据\n6. 统计某学生的的平均成绩\n7. 输出学生名单\n8. 退出系统\n")
        if choice == '1':
            givescore(ID)
        elif choice == '2':
            scletCA()
        elif choice == '3':
            secletclass()
        elif choice == '4':
            Statisticsclass()
        elif choice == '5':
            Statisticsca()
        elif choice == '6':
            Statisticscouse()
        elif choice == '7':
            givestu()
        elif choice == '8':
            break  # 退出系统
        else:
            print("无效选项，请重新选择。")

elif user_power == 3:
    print("教务管理员登录成功！")
    while True:
        choice = input('请选择操作：\n1. 学生表操作\n2. 教师表操作\n3. 班级表操作\n4. 课程表操作\n5. 选课表操作\n6. 备份与恢复\n7. 退出系统\n')
        if choice == '1':
            sturoot()
        elif choice == '2':
            teacherroot()
        elif choice == '3':
            classroot()
        elif choice == '4':
            courseroot()
        elif choice == '5':
            Arrangeroot()
        elif choice == '6':
            while True:
                choice2 = input('请选择操作：\n1.备份数据库\n2.恢复数据库\n3.返回上级\n')
                if choice2 == '1':
                    backup_database(host, user, password, database, backup_file)
                elif choice2 == '2':
                    restore_database(host, user, password, database, backup_file)
                elif choice2 == '3':
                    break
                else:
                    print("无效选项，请重新选择。")
        elif choice == '7':
            break  # 退出系统
        else:
            print("无效选项，请重新选择。")