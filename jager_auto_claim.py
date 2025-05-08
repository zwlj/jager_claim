import time
from web3 import Web3
import json
import os
from typing import Dict, Any, Optional

class JagerContractInteraction:
    def __init__(self, contract_address: str, rpc_url: str, private_key: Optional[str] = None):
        """
        初始化合约交互类
        
        Args:
            contract_address: 合约地址
            rpc_url: BSC RPC URL
            private_key: 私钥（用于发送交易）
        """
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.web3 = Web3(Web3.HTTPProvider(rpc_url))
        self.private_key = private_key
        
        # 合约 ABI
        self.abi = json.loads('''[{"inputs":[{"internalType":"address","name":"jager","type":"address"},{"internalType":"address","name":"airdropAddress","type":"address"}],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[],"name":"LPToken","outputs":[{"internalType":"contract IERC20","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"tokenAmount","type":"uint256"}],"name":"addLiquidity","outputs":[],"stateMutability":"payable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"addReward","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"airdrop","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"claim","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"deposit","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"endBlock","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"jagerToken","outputs":[{"internalType":"contract IJagerHunter","name":"","type":"address"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"lockTime","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"address","name":"account","type":"address"}],"name":"pendingReward","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"poolInfo","outputs":[{"internalType":"uint256","name":"accLPPerShare","type":"uint256"},{"internalType":"uint256","name":"totalAmount","type":"uint256"},{"internalType":"uint256","name":"lastRewardBlock","type":"uint256"},{"internalType":"uint256","name":"totalReward","type":"uint256"},{"internalType":"uint256","name":"releaseReward","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"releaseBlockNumber","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"rewardPerBlock","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"updatePool","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"address","name":"","type":"address"}],"name":"userInfo","outputs":[{"internalType":"uint256","name":"amount","type":"uint256"},{"internalType":"uint256","name":"rewardDebt","type":"uint256"},{"internalType":"uint256","name":"pending","type":"uint256"},{"internalType":"uint256","name":"lockEndedTimestamp","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"amount","type":"uint256"}],"name":"withdraw","outputs":[],"stateMutability":"nonpayable","type":"function"},{"stateMutability":"payable","type":"receive"}]''')
        
        # 初始化合约
        self.contract = self.web3.eth.contract(address=self.contract_address, abi=self.abi)
        
        # 检查连接
        if not self.web3.is_connected():
            raise Exception("无法连接到 BSC 网络")
    
    def get_lp_token_address(self) -> str:
        """获取 LP Token 地址"""
        return self.contract.functions.LPToken().call()
    
    def get_jager_token_address(self) -> str:
        """获取 Jager Token 地址"""
        return self.contract.functions.jagerToken().call()
    
    def get_airdrop_address(self) -> str:
        """获取空投地址"""
        return self.contract.functions.airdrop().call()
    
    def get_end_block(self) -> int:
        """获取结束区块"""
        return self.contract.functions.endBlock().call()
    
    def get_lock_time(self) -> int:
        """获取锁定时间"""
        return self.contract.functions.lockTime().call()
    
    def get_release_block_number(self) -> int:
        """获取释放区块号"""
        return self.contract.functions.releaseBlockNumber().call()
    
    def get_reward_per_block(self) -> int:
        """获取每区块奖励"""
        return self.contract.functions.rewardPerBlock().call()
    
    def get_pool_info(self) -> Dict[str, int]:
        """获取池子信息"""
        result = self.contract.functions.poolInfo().call()
        return {
            "accLPPerShare": result[0],
            "totalAmount": result[1],
            "lastRewardBlock": result[2],
            "totalReward": result[3],
            "releaseReward": result[4]
        }
    
    def get_pending_reward(self, account_address: str) -> int:
        """
        获取待领取奖励
        
        Args:
            account_address: 账户地址
        """
        account_address = Web3.to_checksum_address(account_address)
        return self.contract.functions.pendingReward(account_address).call()
    
    def get_user_info(self, account_address: str) -> Dict[str, int]:
        """
        获取用户信息
        
        Args:
            account_address: 账户地址
        """
        account_address = Web3.to_checksum_address(account_address)
        result = self.contract.functions.userInfo(account_address).call()
        return {
            "amount": result[0],
            "rewardDebt": result[1],
            "pending": result[2],
            "lockEndedTimestamp": result[3]
        }
    
    def _build_and_send_tx(self, function, value=0):
        """
        构建并发送交易
        
        Args:
            function: 合约函数
            value: 发送的 BNB 数量（单位：wei）
        """
        if not self.private_key:
            raise Exception("需要提供私钥才能发送交易")
        
        account = self.web3.eth.account.from_key(self.private_key)
        address = account.address
        
        # 获取 nonce
        nonce = self.web3.eth.get_transaction_count(address)
        
        # 构建交易
        tx = function.build_transaction({
            'from': address,
            'value': value,
            'gas': 2000000,  # 可以根据需要调整
            'gasPrice': self.web3.eth.gas_price,
            'nonce': nonce,
        })
        
        # 签名交易
        signed_tx = self.web3.eth.account.sign_transaction(tx, self.private_key)
        
        # 发送交易 - 兼容不同版本的 Web3.py
        raw_tx = None
        if hasattr(signed_tx, 'rawTransaction'):
            raw_tx = signed_tx.rawTransaction
        elif hasattr(signed_tx, 'raw_transaction'):
            raw_tx = signed_tx.raw_transaction
        else:
            # 尝试获取原始交易数据
            for attr_name in dir(signed_tx):
                if 'raw' in attr_name.lower() and not attr_name.startswith('_'):
                    raw_tx = getattr(signed_tx, attr_name)
                    break
        
        if not raw_tx:
            raise Exception("无法获取签名交易的原始数据，请检查 Web3.py 版本")
        
        # 发送交易
        tx_hash = self.web3.eth.send_raw_transaction(raw_tx)
        
        # 等待交易确认
        receipt = self.web3.eth.wait_for_transaction_receipt(tx_hash)
        
        return receipt
    
    def add_liquidity(self, token_amount: int, bnb_amount: int) -> Dict[str, Any]:
        """
        添加流动性
        
        Args:
            token_amount: 代币数量
            bnb_amount: BNB 数量（单位：wei）
        """
        function = self.contract.functions.addLiquidity(token_amount)
        return self._build_and_send_tx(function, bnb_amount)
    
    def add_reward(self, amount: int) -> Dict[str, Any]:
        """
        添加奖励
        
        Args:
            amount: 奖励数量
        """
        function = self.contract.functions.addReward(amount)
        return self._build_and_send_tx(function)
    
    def claim(self) -> Dict[str, Any]:
        """领取奖励"""
        function = self.contract.functions.claim()
        return self._build_and_send_tx(function)
    
    def deposit(self, amount: int) -> Dict[str, Any]:
        """
        存款
        
        Args:
            amount: 存款数量
        """
        function = self.contract.functions.deposit(amount)
        return self._build_and_send_tx(function)
    
    def update_pool(self) -> Dict[str, Any]:
        """更新池子"""
        function = self.contract.functions.updatePool()
        return self._build_and_send_tx(function)
    
    def withdraw(self, amount: int) -> Dict[str, Any]:
        """
        提款
        
        Args:
            amount: 提款数量
        """
        function = self.contract.functions.withdraw(amount)
        return self._build_and_send_tx(function)


# 使用示例
if __name__ == "__main__":
    # 配置参数
    CONTRACT_ADDRESS = "0x5C08E98F14e462B75C9b3566128f75915B78aee7"  # 替换为实际合约地址
    BSC_RPC_URL = "bsc主网RPC"  # BSC 主网 RPC
    # BSC_RPC_URL = "https://data-seed-prebsc-1-s1.binance.org:8545/"  # BSC 测试网 RPC
    PRIVATE_KEY = "你的私钥"
    #你想要大于多少奖励的时候领一次，单位是M(百万)
    reward = 13784
    
    # 初始化合约交互对象
    jager = JagerContractInteraction(
        contract_address=CONTRACT_ADDRESS,
        rpc_url=BSC_RPC_URL,
        private_key=PRIVATE_KEY  # 仅查询不需要私钥
    )
    pending = 0
    while True:
         # 查询示例
        try:
            # 获取 LP Token 地址
            lp_token = jager.get_lp_token_address()
            print(f"LP Token 地址: {lp_token}")
            
            # 获取用户信息 (替换为你要查询的地址)
            user_address = "你的地址"
            
            # 获取待领取奖励
            pending = jager.get_pending_reward(user_address)
            pending = pending / 10**18 /1000000
            print(f"待领取奖励: {pending:.2f}")
            if pending > reward :
                print("开始领取奖励")
                receipt = jager.claim()
                print(f"存款交易哈希: {receipt.transactionHash.hex()}")
            
        except Exception as e:
            print(f"发生错误: {e}")
        
        print("等待60秒,减少RPC的负担")
        time.sleep(60)
        
    
    