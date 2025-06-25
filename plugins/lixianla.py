# plugins/lixianla.py

async def login(self):
    try:
        # 更新为新的登录页面 URL
        async with self.session.get(f"{self.base_url}/user-login.htm") as response:
            if response.status != 200:
                raise Exception(f"获取登录页面失败，状态码: {response.status}")
            text = await response.text()
            soup = BeautifulSoup(text, 'html.parser')
            
            # 查找CSRF令牌（如果有）
            csrf_token = None
            csrf_input = soup.find('input', {'name': '_token'})
            if csrf_input:
                csrf_token = csrf_input.get('value')
                
            # 准备登录数据
            login_data = {
                'email': self.username,
                'password': self.password,
                'remember': 'on'
            }
            
            if csrf_token:
                login_data['_token'] = csrf_token

        # 更新为新的登录提交 URL（如果需要）
        async with self.session.post(
            f"{self.base_url}/user-login.htm",  # 确认实际的登录提交URL
            data=login_data
        ) as response:
            if response.status != 200:
                raise Exception(f"登录失败，状态码: {response.status}")
            # 检查登录是否成功
            if "用户中心" in await response.text():
                logging.info(f"{self.name} 登录成功")
                return True
            else:
                logging.error(f"{self.name} 登录失败")
                return False
    except Exception as e:
        logging.error(f"{self.name} 登录异常: {str(e)}")
        return False
