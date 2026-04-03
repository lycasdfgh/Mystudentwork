create database end;
use end;

#教务管理员
CREATE TABLE School(
	RootID INT PRIMARY KEY,
	Name VARCHAR(10),
	Power INT DEFAULT 3
);

#教师表
CREATE TABLE Teachers (
    TeacherID INT PRIMARY KEY,
    Name VARCHAR(10),
    Power INT DEFAULT 2
);

#班级表
CREATE TABLE Classes (
    ClassID INT PRIMARY KEY,
    ClassName VARCHAR(20)
);

#学生表
CREATE TABLE Students (
    StudentID INT PRIMARY KEY,
    Name VARCHAR(10),
    Power INT DEFAULT 1,
    ClassID INT,
    Endscore decimal(10,2),
    FOREIGN KEY (ClassID) REFERENCES Classes(ClassID)
);

#课程表
CREATE TABLE Courses (
    CourseID INT PRIMARY KEY,
    CourseName VARCHAR(10),
    Credit INT #课程学分
);

#选课安排表
CREATE TABLE CourseArrangements (
    ArrangementID INT PRIMARY KEY,
    CourseID INT,
    TeacherID INT,
    StartTime INT,  #选课开始时间
    EndTime INT,    #选课结束时间
    InTime INT,     #成绩录入结束时间
    StudentLimit INT,#限制选课人数
    FOREIGN KEY (CourseID) REFERENCES Courses(CourseID),
    FOREIGN KEY (TeacherID) REFERENCES Teachers(TeacherID)
);

#选课记录表与成绩
CREATE TABLE Enrollments (
    StudentID INT,
    ArrangementID INT, #已安排的课程编号
    Score INT DEFAULT 0,#记录选课成绩
    PRIMARY KEY(StudentID,ArrangementID),
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (ArrangementID) REFERENCES CourseArrangements(ArrangementID)
);

#学生表视图
CREATE VIEW StudentInfo AS
SELECT StudentID, Name, ClassID
FROM Students;

#------------------------------------触发器------------------------------------#
#学籍分触发器
DELIMITER //
CREATE TRIGGER UpdateEndscore AFTER UPDATE ON Enrollments
FOR EACH ROW
BEGIN
  -- Calculate the sum of (score * credit) for all courses the student is enrolled in
  DECLARE total_score DECIMAL(10,2) DEFAULT 0;#声明变量
  DECLARE total_credit INT DEFAULT 0;

  SELECT SUM(e.Score * c.Credit), SUM(c.Credit)
  INTO total_score, total_credit
  FROM Enrollments e
  JOIN CourseArrangements ca ON e.ArrangementID = ca.ArrangementID
  JOIN Courses c ON ca.CourseID = c.CourseID
  WHERE e.StudentID = NEW.StudentID;

  -- Update the student's Endscore
  UPDATE Students
  SET Endscore = IF(total_credit > 0, total_score / total_credit, 0)
  WHERE StudentID = NEW.StudentID;
END //
DELIMITER ;

#限制选课人数触发器
DELIMITER //
CREATE TRIGGER CheckStudentLimit BEFORE INSERT ON Enrollments
FOR EACH ROW
BEGIN
  DECLARE current_count INT;
  SELECT COUNT(*) INTO current_count
  FROM Enrollments
  WHERE ArrangementID = NEW.ArrangementID;

  IF current_count >= (SELECT StudentLimit FROM CourseArrangements WHERE ArrangementID = NEW.ArrangementID) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = '选课人数已达上限';
  END IF;
END //
DELIMITER ;

#限制同课不同老师的选择
DELIMITER //
CREATE TRIGGER BeforeEnrollTrigger BEFORE INSERT ON Enrollments
FOR EACH ROW
BEGIN
    -- 定义一个变量来存储查询结果
    DECLARE duplicateEnrollmentCount INT DEFAULT 0;

    -- 检查是否已经存在相同CourseID但不同ArrangementID的选课记录
    SELECT COUNT(*) INTO duplicateEnrollmentCount
    FROM Enrollments e
    JOIN CourseArrangements ca ON e.ArrangementID = ca.ArrangementID
    WHERE e.StudentID = NEW.StudentID
    AND ca.CourseID = (SELECT CourseID FROM CourseArrangements WHERE ArrangementID = NEW.ArrangementID)
    AND e.ArrangementID <> NEW.ArrangementID;

    -- 如果存在重复选课，则抛出异常
    IF duplicateEnrollmentCount > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = '不能选择不同老师教的同一个课程。';
    END IF;
END//
DELIMITER ;

#删除学生触发器
DELIMITER //
CREATE TRIGGER DeleteStudentEnrollments
BEFORE DELETE ON Students
FOR EACH ROW
BEGIN
    -- 声明一个变量来存储被删除学生的ID
    DECLARE deletedStudentID INT;

    -- 将被删除学生的ID赋值给变量
    SET deletedStudentID = OLD.StudentID;

    -- 执行删除操作，删除Enrollments表中与被删除学生相关的记录
    DELETE FROM Enrollments
    WHERE StudentID = deletedStudentID;
END//
DELIMITER ;

#删除教师触发器
DELIMITER //
CREATE TRIGGER DeleteTeacherCascade
BEFORE DELETE ON Teachers
FOR EACH ROW
BEGIN
    -- 删除与该教师相关的课程安排
    DELETE FROM CourseArrangements WHERE TeacherID = OLD.TeacherID;
END//
DELIMITER ;
DELIMITER //
CREATE TRIGGER DeleteArrangementCascade
BEFORE DELETE ON CourseArrangements
FOR EACH ROW
BEGIN
    -- 删除与该课程安排相关的选课记录
    DELETE FROM Enrollments WHERE ArrangementID = OLD.ArrangementID;
END//
DELIMITER ;

#删除班级触发器
DELIMITER //
CREATE TRIGGER DeleteClassCascade
BEFORE DELETE ON Classes
FOR EACH ROW
BEGIN
    -- 删除与被删除班级对应的所有学生记录
    DELETE FROM Students WHERE ClassID = OLD.ClassID;
END//
DELIMITER ;

#删除选课触发器
DELIMITER //
CREATE TRIGGER DeleteArrangementCascade2
BEFORE DELETE ON CourseArrangements
FOR EACH ROW
BEGIN
    -- 删除与被删除安排相关的所有选课记录
    DELETE FROM Enrollments WHERE ArrangementID = OLD.ArrangementID;
END//
DELIMITER ;

#删除课程触发器
DELIMITER //
CREATE TRIGGER DeleteCourseCascade
BEFORE DELETE ON Courses
FOR EACH ROW
BEGIN
    -- 首先，删除与该课程ID相关的所有选课安排
    DELETE FROM CourseArrangements WHERE CourseID = OLD.CourseID;
    -- 由于外键约束，Enrollments表中与这些安排ID相关的记录将自动被删除
END//
DELIMITER ;

#--------------------------------------触发器结束---------------------------#

#--------------------------------------存储过程------------------------------#
#输出学生名单报表存储过程
DELIMITER //
CREATE PROCEDURE GetStudentsByClass(IN classIDParam INT)
BEGIN
    -- 使用SELECT语句直接返回结果，而不是使用游标
    SELECT
        StudentID,
        Name,
        Endscore
    FROM
        Students
    WHERE
        ClassID = classIDParam;
END//
DELIMITER ;

CALL GetStudentsByClass();

#----------------------------------------存储过程结束------------------------#

#----------------------------------------数据录入---------------------------------#

INSERT INTO School (RootID, Name)
VALUES
(3001,'root1'),
(3002,'root2');

INSERT INTO Teachers (TeacherID, Name)
VALUES
(2001,'teacher1'),
(2002,'teacher2'),
(2003,'teacher3'),
(2004,'teacher4');

INSERT INTO Classes (ClassID, ClassName)
VALUES
(202201,'22计科1班'),
(202202,'22计科2班'),
(202203,'22计科3班'),
(202204,'22计科4班');

INSERT INTO Students (StudentID, Name, ClassID)
VALUES
(1001,'student1',202201),
(1002,'student2',202202),
(1003,'student3',202203),
(1004,'student4',202204),
(1005,'student5',202203);

INSERT INTO Courses (CourseID, CourseName, Credit)
VALUES
(1,'数据库',3),
(2,'计算机网络',2),
(3,'计算机组成',2);

INSERT INTO CourseArrangements (ArrangementID, CourseID, TeacherID, StartTime, EndTime, InTime, StudentLimit)
VALUES
(1,1,2001,20240301,20240420,20240701,2),
(2,1,2002,20240301,20240520,20240701,20),
(3,2,2003,20240301,20240525,20240701,20),
(4,3,2004,20240301,20240619,20240701,20),
(5,3,2001,20240301,20240630,20240701,20);

INSERT INTO Enrollments (StudentID ,ArrangementID )
VALUES
(1001,1),
(1001,3),
(1002,2),
(1003,3),
(1003,5),
(1004,3),
(1004,4),
(1005,2),
(1005,3);




#需求变更
-- 添加冗余列
ALTER TABLE Students
ADD GPA FLOAT; -- 用于存储绩点分

-- 创建课程成绩绩点表
CREATE TABLE GradePointTable (
    Code INT PRIMARY KEY,
    MinScore FLOAT,
    MaxScore FLOAT,
    GradePoint FLOAT
);

-- 插入课程成绩绩点数据
INSERT INTO GradePointTable (Code, MinScore, MaxScore, GradePoint)
VALUES
(1, 0, 59.99, 0),
(2, 60, 69.99, 1),
(3, 70, 79.99, 2),
(4, 80, 89.99, 3),
(5, 90, 100, 4);

-- 创建触发器，每次更新学生成绩时计算绩点分
DELIMITER //
CREATE TRIGGER UpdateGPA
AFTER UPDATE ON Enrollments
FOR EACH ROW
BEGIN
    DECLARE totalCredits INT;
    DECLARE totalGradePoints FLOAT;
    DECLARE gpa FLOAT;

    SELECT SUM(C.Credit), SUM(G.GradePoint * C.Credit)
    INTO totalCredits, totalGradePoints
    FROM Enrollments AS E
    JOIN CourseArrangements AS CA ON E.ArrangementID = CA.ArrangementID
    JOIN Courses AS C ON CA.CourseID = C.CourseID
    JOIN GradePointTable AS G ON E.Score BETWEEN G.MinScore AND G.MaxScore
    WHERE E.StudentID = NEW.StudentID;

    SET gpa = totalGradePoints / totalCredits;

    UPDATE Students
    SET GPA = gpa
    WHERE StudentID = NEW.StudentID;
END //
DELIMITER ;
