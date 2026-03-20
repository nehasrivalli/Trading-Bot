import numpy as np
import pandas as pd
import gym
from gym import spaces
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv

class TradingEnvironment(gym.Env):
    """Custom Trading Environment that follows gym interface"""
    
    def __init__(self, df):
        super(TradingEnvironment, self).__init__()
        
        self.df = df
        self.reward_range = (-np.inf, np.inf)
        
        # Actions: 0 = Hold, 1 = Buy, 2 = Sell
        self.action_space = spaces.Discrete(3)
        
        # Observation space: OHLCV data + technical indicators
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(10,), dtype=np.float32
        )
        
        self.reset()
        
    def reset(self):
        self.current_step = 0
        self.balance = 10000.0
        self.shares_held = 0
        self.net_worth = self.balance
        self.max_net_worth = self.net_worth
        self.returns = []
        
        return self._next_observation()
        
    def _next_observation(self):
        # Get the data point for the current step
        frame = self.df.iloc[self.current_step]
        
        # Normalize the data
        obs = np.array([
            frame['Open'] / 1000,
            frame['High'] / 1000,
            frame['Low'] / 1000,
            frame['Close'] / 1000,
            frame['Volume'] / 1000000,
            frame['RSI'] / 100 if 'RSI' in frame else 0,
            frame['MACD'] / 100 if 'MACD' in frame else 0,
            frame['BB_upper'] / 1000 if 'BB_upper' in frame else 0,
            frame['BB_lower'] / 1000 if 'BB_lower' in frame else 0,
            self.shares_held / 100
        ])
        
        return obs
        
    def step(self, action):
        # Get current price
        current_price = self.df.iloc[self.current_step]['Close']
        
        # Execute action
        if action == 1:  # Buy
            # Calculate maximum shares we can buy
            max_shares = self.balance // current_price
            # Buy 10% of max shares
            shares_to_buy = max(1, int(max_shares * 0.1))
            cost = shares_to_buy * current_price
            
            if cost <= self.balance:
                self.balance -= cost
                self.shares_held += shares_to_buy
        
        elif action == 2:  # Sell
            if self.shares_held > 0:
                # Sell all shares
                self.balance += self.shares_held * current_price
                self.shares_held = 0
        
        # Move to next step
        self.current_step += 1
        
        # Calculate reward
        self.net_worth = self.balance + self.shares_held * current_price
        reward = self.net_worth - self.max_net_worth
        self.max_net_worth = max(self.max_net_worth, self.net_worth)
        
        # Check if done
        done = self.current_step >= len(self.df) - 1
        
        # Get next observation
        obs = self._next_observation() if not done else None
        
        return obs, reward, done, {}
    
    def render(self, mode='human'):
        profit = self.net_worth - 10000
        print(f"Step: {self.current_step}")
        print(f"Balance: ${self.balance:.2f}")
        print(f"Shares held: {self.shares_held}")
        print(f"Net worth: ${self.net_worth:.2f}")
        print(f"Profit: ${profit:.2f}")

def train_rl_model(data_file="BTC-USD.csv"):
    # Load and prepare data
    df = pd.read_csv(data_file)
    
    # Add technical indicators
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_lower'] = bb.bollinger_lband()
    
    # Drop NaN values
    df = df.dropna()
    
    # Create environment
    env = DummyVecEnv([lambda: TradingEnvironment(df)])
    
    # Train model
    model = PPO("MlpPolicy", env, verbose=1)
    model.learn(total_timesteps=10000)
    
    # Save model
    model.save("ppo_trading_model")
    
    return model

def test_rl_model(model_path="ppo_trading_model", data_file="BTC-USD_test.csv"):
    # Load test data
    df = pd.read_csv(data_file)
    
    # Add technical indicators
    df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
    macd = ta.trend.MACD(df['Close'])
    df['MACD'] = macd.macd()
    bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
    df['BB_upper'] = bb.bollinger_hband()
    df['BB_lower'] = bb.bollinger_lband()
    
    # Drop NaN values
    df = df.dropna()
    
    # Create environment
    env = DummyVecEnv([lambda: TradingEnvironment(df)])
    
    # Load model
    model = PPO.load(model_path)
    
    # Test model
    obs = env.reset()
    done = False
    total_reward = 0
    
    while not done:
        action, _ = model.predict(obs)
        obs, reward, done, _ = env.step(action)
        total_reward += reward[0]
        env.render()
    
    print(f"Total reward: {total_reward}")

if __name__ == "__main__":
    import ta
    import yfinance as yf
    
    # Download data
    data = yf.download("BTC-USD", start="2022-01-01", end="2023-01-01")
    data.to_csv("BTC-USD.csv")
    
    test_data = yf.download("BTC-USD", start="2023-01-01", end="2023-06-01")
    test_data.to_csv("BTC-USD_test.csv")
    
    # Train model
    model = train_rl_model()
    
    # Test model
    test_rl_model()