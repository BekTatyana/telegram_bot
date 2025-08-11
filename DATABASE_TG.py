from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv
from logg import logger
from telebot_import import bot
import os 

load_dotenv()
Base = declarative_base()


class User(Base):
    __tablename__ = 'Name'
    user_id = Column(Integer, primary_key=True)
    username = Column(String(25), unique=True, nullable=False)
    tasks = relationship("Task", back_populates="user", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = 'Task'
    task_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('Name.user_id'), nullable=False)
    task = Column(Text, nullable=False)
    user = relationship("User", back_populates="tasks")

class Database:
    def __init__(self):
        try:

            database_url = os.getenv("url")
            self.engine = create_engine(database_url, echo=False)
            Base.metadata.create_all(self.engine)
            Session = sessionmaker(bind=self.engine)
            self.session = Session()
            logger.info("Связь с базой данных установлена")

        except SQLAlchemyError as e:
            logger.error(f"Ошибка при подключении к базе данных: {e}")
            raise

    def close_session(self):
        self.session.close()
        logger.info("Сессия базы данных закрыта")

    def save_tasks(self, username, tasks,chat_id):
        try:
            user = self.session.query(User).filter_by(username=username).first()
            if not user:
                user = User(username=username)
                self.session.add(user)
                self.session.flush()
            
            for task in tasks:
                if task:
                    new_task = Task(task=task, user=user)
                    self.session.add(new_task)
            
            self.session.commit()
            bot.send_message(chat_id,f"Задачи пользователя {username} успешно сохранены")

        except Exception as e:
            self.session.rollback()
            bot.callback_query_handler(f"Ошибка при добавлении задач: {e}")
        finally: 
            self.session.close()
          

    def get_all_info(self,chat_id):
        try:
            users = self.session.query(User).order_by(User.username).all()
            tasks = self.session.query(Task).order_by(Task.task).all()
            if not users or not tasks:
                bot.send_message(chat_id,"В базе данных нет данных")
                return
            
            full_info = '\nЗадачи всех пользователей:'
            for user in users:
                if  not user.tasks: 
                    continue 
                full_info+= f"\n\nПользователь: {user.username}"
                for task in user.tasks:
                    full_info+= f"\nID: {task.task_id}: {task.task}"
            bot.send_message(chat_id,full_info)
        except Exception as e:
            bot.send_message(chat_id,"Ошибка при получении данных")
            logger.error(f"Ошибка при получении данных: {e}")\
            
        finally: 
            self.session.close()

    def delete_user_tasks(self, username,chat_id):
        try:
            user = self.session.query(User).filter_by(username=username).first()
            if not user:
                bot.send_message(chat_id,f"Пользователь {username} не найден")
                self.session.close()
                return
            
            self.session.query(Task).filter(Task.user_id == user.user_id).delete()
            self.session.commit()
            bot.send_message(chat_id, f'Задачи пользователя {username} успешно удалены')
        except Exception as e:
            self.session.rollback()
            logger.error(f"Ошибка при удалении задач пользователя: {e}")
        finally: 
            self.session.close()

    def delete_all(self,chat_id):
        try:
            self.session.query(Task).delete()
            self.session.query(User).delete()
            self.session.commit()
            bot.send_message(chat_id,"Все данные удалены из базы")
            
        except Exception as e:
            self.session.rollback()
            self.session.close()
            bot.send_message(chat_id,"Ошибка при удалении всех данных")
            logger.error(e)

        finally: 
            self.session.close()    

    def delete_only_id_tasks(self, task_ids,chat_id):
        try:   
            ids = list(set(int(id_) for id_ in task_ids if id_.isdigit()))

            if not ids:
                bot.send_message(chat_id,"Нет корректных ID для удаления")
                return
            
            self.session.query(Task).filter(Task.task_id.in_(ids)).delete()
            self.session.commit()
            bot.send_message(chat_id,"Я удалил все задачи, которые нашел!!!")

        except Exception as e:
            self.session.rollback()
            logger.error(f"Ошибка при удалении задач по ID: {e}")
            bot.send_message(chat_id,"Ошибка при удалении задач по ID")
            return
        
        finally: 
            self.session.close()