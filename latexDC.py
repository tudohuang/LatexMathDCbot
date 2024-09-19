import os
import nextcord
from nextcord.ext import commands
import matplotlib.pyplot as plt
import io
import re
import sympy as sp
from dotenv import load_dotenv

load_dotenv()

intents = nextcord.Intents.default()
intents.message_content = True

# 讀取環境變數中的 TOKEN
TOKEN = os.getenv("DISCORD_TOKEN")

bot = commands.Bot(intents=intents)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')

# 動態計算圖像寬度，讓公式顯示更適中
def calculate_fig_width(latex_content):
    max_length = max([len(line) for line in latex_content.splitlines()])
    return max(4, 0.1 * max_length)  # 增加最小寬度為 4，並增強每行字符的寬度

# 動態調整字體大小，根據行數和字符長度
def calculate_font_size(latex_content):
    lines = latex_content.splitlines()
    max_length = max([len(line) for line in lines])
    if max_length > 50 or len(lines) > 5:
        return 30  # 若字符過多或行數過多，使用稍小字體
    elif max_length > 30 or len(lines) > 3:
        return 16  # 中等字體
    else:
        return 12  # 大字體

# 渲染 LaTeX 公式
async def render_latex(latex_content, bg_color, font_color, interaction):
    try:
        formulas = latex_content.splitlines()

        fig_width = calculate_fig_width(latex_content)
        fig_height = 0.4 + len(formulas) * 0.3  # 動態調整高度
        font_size = calculate_font_size(latex_content)  # 動態調整字體大小
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
        ax.set_facecolor('none')  # 設置透明背景
        fig.patch.set_facecolor('none')
        ax.axis('off')

        for i, formula in enumerate(formulas):
            formula = formula.strip()
            if formula:
                ax.text(0.5, 0.9 - i * 0.3, f'${formula}$', fontsize=font_size, ha='center', va='top', color=font_color)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)  # 透明背景
        buf.seek(0)
        plt.close(fig)

        await interaction.response.send_message(file=nextcord.File(buf, 'latex.png'))

    except Exception as e:
        await interaction.response.send_message(f"無法轉換為 LaTeX: {str(e)}")

# 解決數學方程
async def solve_math(equation, interaction):
    try:
        x = sp.symbols('x')
        if "diff" in equation:
            y = sp.Function('y')(x)
            eq = sp.sympify(equation)
            solution = sp.dsolve(eq, y)
            latex_solution = sp.latex(solution)
        else:
            lhs, rhs = equation.split('=')
            eq = sp.Eq(sp.sympify(lhs), sp.sympify(rhs))
            solution = sp.solve(eq, x)
            latex_solution = sp.latex(solution)

        fig, ax = plt.subplots(figsize=(6, 3), dpi=300)
        ax.text(0.5, 0.5, f'Solution: ${latex_solution}$', fontsize=22, ha='center', va='center', color='white')
        ax.set_facecolor('none')
        fig.patch.set_facecolor('none')
        ax.axis('off')

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)
        buf.seek(0)
        plt.close(fig)

        await interaction.response.send_message(file=nextcord.File(buf, 'solution.png'))
    except Exception as e:
        await interaction.response.send_message(f"無法解決該方程: {str(e)}")

# /latex 命令
@bot.slash_command(name="latex", description="輸入 LaTeX 公式")
async def latex(
    interaction: nextcord.Interaction,
    formula: str,
    bg_color: str = 'none',  # 默認背景設置為透明
    font_color: str = 'white'  # 默認字體顏色
):
    await render_latex(formula, bg_color, font_color, interaction)

# /solve 命令
@bot.slash_command(name="solve", description="解決數學方程")
async def solve(
    interaction: nextcord.Interaction,
    equation: str
):
    await solve_math(equation, interaction)

# 啟動 bot
if __name__ == "__main__":
    bot.run(TOKEN)
