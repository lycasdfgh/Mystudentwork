from cryptography.fernet import Fernet
import os
import hashlib
import base64
import shutil

class FileEncryptionSystem:
    def __init__(self, password_file):
        self.password_file = password_file
        self.passwords = []  # 用于存储所有口令的哈希
        self.keys = []  # 用于存储所有密钥
        self.key = self._load_key()
        self.cipher_suite = Fernet(self.key)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def _load_key(self):
        try:
            with open(self.password_file, 'r') as f:
                for line in f:
                    self.passwords.append(line.strip())
                # 获取最后一个密钥
                key = base64.urlsafe_b64decode(self.passwords[-1])
                self.keys.append(self.passwords[-1])  # 存储密钥
                return key
        except (FileNotFoundError, ValueError, IndexError):
            # 如果文件不存在，创建新密钥和口令
            initial_password = input("请输入初始口令：")
            password_hash = self._hash_password(initial_password)
            new_key = Fernet.generate_key()
            with open(self.password_file, 'w') as f:
                f.write(password_hash + '\n')
                f.write(base64.urlsafe_b64encode(new_key).decode() + '\n')
            self.passwords.append(password_hash)
            self.keys.append(base64.urlsafe_b64encode(new_key).decode())
            return new_key

    def encrypt_file(self, input_path, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(input_path, 'rb') as file:
            original_file_data = file.read()

        encrypted_data = self.cipher_suite.encrypt(original_file_data)

        file_name = os.path.basename(input_path)
        output_path = os.path.join(output_dir, file_name)

        with open(output_path, 'wb') as encrypted_file:
            encrypted_file.write(encrypted_data)

        shutil.move(input_path, output_path)
        print(f"文件已加密并移动到 {output_path}")

    def decrypt_file(self, input_path, output_dir):
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        with open(input_path, 'rb') as encrypted_file:
            encrypted_data = encrypted_file.read()

        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
        except Exception as e:
            print("解密失败，可能是文件已损坏或密钥不正确。")
            return

        file_name = os.path.basename(input_path)
        output_path = os.path.join(output_dir, file_name)

        with open(output_path, 'wb') as file:
            file.write(decrypted_data)

        shutil.move(input_path, output_path)
        print(f"文件已解密并移动到 {output_path}")

    def change_password(self, old_password, new_password):
        old_hash = self._hash_password(old_password)
        if old_hash in self.passwords:  # 检查旧密码是否正确
            new_hash = self._hash_password(new_password)
            self.passwords.append(new_hash)  # 添加新密码哈希
            new_key = self._generate_key(new_password)  # 生成新密钥
            self.keys.append(base64.urlsafe_b64encode(new_key).decode())  # 存储新密钥
            self.cipher_suite = Fernet(new_key)  # 更新加密套件
            # 更新密码文件中的密码哈希和密钥
            with open(self.password_file, 'w') as f:
                for hash in self.passwords:
                    f.write(hash + '\n')
            print("口令修改成功。")
        else:
            print("旧口令不正确，无法修改口令。")

    def restore_password(self):
        if len(self.passwords) > 1:  # 确保有口令可以恢复
            self.passwords.pop()  # 删除最新口令
            self.keys.pop()  # 删除最新密钥
            # 获取上一个密钥
            key = base64.urlsafe_b64decode(self.keys[-1])
            self.key = key
            self.cipher_suite = Fernet(self.key)
            print("口令恢复成功。")
        else:
            print("没有旧口令可恢复。")

    def _generate_key(self, password):
        # 使用密码生成密钥
        return base64.urlsafe_b64encode(hashlib.sha256(password.encode()).digest())

def main():
    password_file = r'C:\Users\lyc26\Desktop\password.txt'
    system = FileEncryptionSystem(password_file)

    while True:
        print("\n1. 加密并导入文件")
        print("2. 解密并导出文件")
        print("3. 修改口令")
        print("4. 恢复口令")
        print("5. 退出")

        choice = input("请选择一个选项： ")

        if choice == '1':
            file_path = input("请输入要加密的文件路径：")
            encrypted_dir = input("请输入加密文件保存目录：")
            system.encrypt_file(file_path, encrypted_dir)

        elif choice == '2':
            file_path = input("请输入要解密的加密文件路径：")
            decrypted_dir = input("请输入解密文件保存目录：")
            system.decrypt_file(file_path, decrypted_dir)

        elif choice == '3':
            old_password = input("请输入当前口令：")
            new_password = input("请输入新口令：")
            system.change_password(old_password, new_password)

        elif choice == '4':
            system.restore_password()

        elif choice == '5':
            os.remove(password_file)  # 删除密码文件
            print("程序已退出，所有口令已删除。")
            break
        else:
            print("无效的选择，请重新输入。")

if __name__ == "__main__":
    main()