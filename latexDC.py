import os
import nextcord
from nextcord.ext import commands
import matplotlib.pyplot as plt
import io
import re
import sympy as sp
import numpy as np
from flask import Flask
import threading

# Flask 伺服器 (Keep-alive 機制)
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is alive!"

def run_keep_alive():
    app.run(host="0.0.0.0", port=8080)

# 啟動 Flask 伺服器
keep_alive_thread = threading.Thread(target=run_keep_alive)
keep_alive_thread.start()

# 讀取環境變數
TOKEN = os.getenv("DISCORD_TOKEN")

# 確保 TOKEN 存在，避免部署後出錯
if not TOKEN:
    raise ValueError("DISCORD_TOKEN is not set in the environment variables.")

# Discord Bot 初始化
intents = nextcord.Intents.default()
intents.message_content = True
bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f"{bot.user} logged in!")

# 繪製 LaTeX 圖形
async def render_latex(latex_content, bg_color, font_color, interaction):
    try:
        await interaction.response.defer()
        formulas = latex_content.splitlines()
        fig_width = max(4, 0.1 * max([len(line) for line in latex_content.splitlines()]))
        fig_height = 0.4 + len(formulas) * 0.3
        font_size = max(12, min(30, int(0.5 * len(latex_content))))
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
        ax.set_facecolor(bg_color)
        ax.axis('off')

        for i, formula in enumerate(formulas):
            formula = formula.strip()
            if formula:
                ax.text(0.5, 0.9 - i * 0.3, f'${formula}$', fontsize=font_size, ha='center', va='top', color=font_color)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)
        buf.seek(0)
        plt.close(fig)

        await interaction.followup.send(file=nextcord.File(buf, 'latex.png'))
    except Exception as e:
        await interaction.followup.send(f"無法轉換為 LaTeX: {str(e)}")

# LaTeX 指令
@bot.slash_command(name="latex", description="輸入 LaTeX 公式")
async def latex(interaction: nextcord.Interaction, formula: str, bg_color: str = 'none', font_color: str = 'white'):
    await render_latex(formula, bg_color, font_color, interaction)

# 數學解方程指令
@bot.slash_command(name="solve", description="解決數學方程")
async def solve(interaction: nextcord.Interaction, equation: str):
    try:
        await interaction.response.defer()
        x = sp.symbols('x')
        lhs, rhs = equation.split('=')
        eq = sp.Eq(sp.sympify(lhs), sp.sympify(rhs))
        solution = sp.solve(eq, x)
        latex_solution = sp.latex(solution)

        await interaction.followup.send(f"解方程結果: ${latex_solution}$")
    except Exception as e:
        await interaction.followup.send(f"無法解決該方程: {str(e)}")

# 繪製數學函數圖像
@bot.slash_command(name="plot", description="繪製數學函數圖像")
async def plot_function(interaction: nextcord.Interaction, equation: str, x_min: float = -10, x_max: float = 10):
    try:
        await interaction.response.defer()
        x = sp.symbols('x')
        expr = sp.sympify(equation)
        f = sp.lambdify(x, expr, "numpy")
        x_vals = np.linspace(x_min, x_max, 500)
        y_vals = f(x_vals)

        fig, ax = plt.subplots(figsize=(6, 4), dpi=300)
        ax.plot(x_vals, y_vals, label=f"y = {equation}")
        ax.axhline(0, color="black", linewidth=0.5, linestyle="--")
        ax.axvline(0, color="black", linewidth=0.5, linestyle="--")
        ax.grid(color="gray", linestyle="--", linewidth=0.5)
        ax.legend()
        ax.set_xlabel("x")
        ax.set_ylabel("y")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        await interaction.followup.send(file=nextcord.File(buf, 'plot.png'))
    except Exception as e:
        await interaction.followup.send(f"無法繪製圖形: {str(e)}")

# 矩陣運算指令
@bot.slash_command(name="matrix", description="執行矩陣運算")
async def matrix_calc(interaction: nextcord.Interaction, matrix1: str, matrix2: str = None, operation: str = "multiply"):
    try:
        await interaction.response.defer()
        m1 = np.array(eval(matrix1))
        if matrix2:
            m2 = np.array(eval(matrix2))

        if operation == "multiply":
            result = np.dot(m1, m2)
        elif operation == "transpose":
            result = m1.T
        elif operation == "inverse":
            result = np.linalg.inv(m1)
        else:
            raise ValueError("未知矩陣操作")

        await interaction.followup.send(f"矩陣運算結果: \n{result}")
    except Exception as e:
        await interaction.followup.send(f"無法執行矩陣運算: {str(e)}")

# 傅立葉變換
@bot.slash_command(name="fourier", description="計算傅立葉變換或逆變換")
async def fourier_transform(interaction: nextcord.Interaction, function: str, transform_type: str = "forward"):
    try:
        await interaction.response.defer()
        x, k = sp.symbols('x k')
        expr = sp.sympify(function)

        if transform_type == "forward":
            ft = sp.fourier_transform(expr, x, k)
        elif transform_type == "inverse":
            ft = sp.inverse_fourier_transform(expr, k, x)
        else:
            raise ValueError("未知的傅立葉變換類型")

        latex_result = sp.latex(ft)
        await interaction.followup.send(f"傅立葉變換結果: $${latex_result}$$")
    except Exception as e:
        await interaction.followup.send(f"無法計算傅立葉變換: {str(e)}")

# 啟動 bot
if __name__ == "__main__":
    bot.run(TOKEN)
