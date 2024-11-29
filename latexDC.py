import os
import nextcord
from nextcord.ext import commands
import matplotlib.pyplot as plt
import io
import re
import sympy as sp
import numpy as np

from dotenv import load_dotenv

load_dotenv()

# Discord Bot 初始化
intents = nextcord.Intents.default()
intents.message_content = True
TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(intents=intents)



@bot.event
async def on_ready():
    # 清除並重新同步指令
    try:
        # 清除所有指令
        await bot.clear_application_commands()
        # 同步所有指令
        synced = await bot.sync_application_commands()
        print(f"已清除並同步 {len(synced)} 個指令: {[cmd.name for cmd in synced]}")
    except Exception as e:
        print(f"同步指令失敗: {e}")

# 動態計算圖像寬度
def calculate_fig_width(latex_content):
    max_length = max([len(line) for line in latex_content.splitlines()])
    return max(4, 0.1 * max_length)

def calculate_font_size(latex_content):
    lines = latex_content.splitlines()
    max_length = max([len(line) for line in lines])
    if max_length > 50 or len(lines) > 5:
        return 30
    elif max_length > 30 or len(lines) > 3:
        return 16
    else:
        return 12

async def render_latex(latex_content, bg_color, font_color, interaction):
    try:
        formulas = latex_content.splitlines()
        fig_width = calculate_fig_width(latex_content)
        fig_height = 0.4 + len(formulas) * 0.3
        font_size = calculate_font_size(latex_content)
        fig, ax = plt.subplots(figsize=(fig_width, fig_height), dpi=300)
        ax.set_facecolor('none')
        fig.patch.set_facecolor('none')
        ax.axis('off')

        for i, formula in enumerate(formulas):
            formula = formula.strip()
            if formula:
                ax.text(0.5, 0.9 - i * 0.3, f'${formula}$', fontsize=font_size, ha='center', va='top', color=font_color)

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight', pad_inches=0, transparent=True)
        buf.seek(0)
        plt.close(fig)

        await interaction.response.send_message(file=nextcord.File(buf, 'latex.png'))
    except Exception as e:
        await interaction.response.send_message(f"無法轉換為 LaTeX: {str(e)}")

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

# 各種指令
@bot.slash_command(name="latex", description="輸入 LaTeX 公式")
async def latex(interaction: nextcord.Interaction, formula: str, bg_color: str = 'none', font_color: str = 'white'):
    await render_latex(formula, bg_color, font_color, interaction)

@bot.slash_command(name="solve", description="解決數學方程")
async def solve(interaction: nextcord.Interaction, equation: str):
    await solve_math(equation, interaction)




@bot.slash_command(name="plot", description="繪製數學函數圖像")
async def plot_function(interaction: nextcord.Interaction, equation: str, x_min: float = -10, x_max: float = 10):
    try:
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
        #ax.set_title("數學函數圖像")
        ax.set_xlabel("x")
        ax.set_ylabel("y")

        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=300, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)

        #await interaction.response.send_message(file=nextcord.File(buf, 'plot.png'))
        await interaction.followup.send(file=nextcord.File(buf, 'plot.png'))
    except Exception as e:
        await interaction.response.send_message(f"無法繪製圖形: {str(e)}")

@bot.slash_command(name="symbolic", description="符號化數學運算")
async def symbolic_math(interaction: nextcord.Interaction, expression: str, operation: str = "simplify"):
    try:
        x = sp.symbols('x')
        expr = sp.sympify(expression)

        if operation == "simplify":
            result = sp.simplify(expr)
        elif operation == "expand":
            result = sp.expand(expr)
        elif operation == "factor":
            result = sp.factor(expr)
        elif operation == "diff":
            result = sp.diff(expr, x)
        elif operation == "integrate":
            result = sp.integrate(expr, x)
        else:
            raise ValueError("未知操作類型")

        latex_result = sp.latex(result)
        await interaction.response.send_message(f"結果: $${latex_result}$$")
    except Exception as e:
        await interaction.response.send_message(f"無法執行符號計算: {str(e)}")

@bot.slash_command(name="matrix", description="執行矩陣運算")
async def matrix_calc(interaction: nextcord.Interaction, matrix1: str, matrix2: str = None, operation: str = "multiply"):
    try:
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

        await interaction.response.send_message(f"矩陣運算結果: \n{result}")
    except Exception as e:
        await interaction.response.send_message(f"無法執行矩陣運算: {str(e)}")

@bot.slash_command(name="fourier", description="計算傅立葉變換或逆變換")
async def fourier_transform(interaction: nextcord.Interaction, function: str, transform_type: str = "forward"):
    try:
        x, k = sp.symbols('x k')
        expr = sp.sympify(function)

        if transform_type == "forward":
            ft = sp.fourier_transform(expr, x, k)
        elif transform_type == "inverse":
            ft = sp.inverse_fourier_transform(expr, k, x)
        else:
            raise ValueError("未知的傅立葉變換類型")

        latex_result = sp.latex(ft)
        await await render_latex(f"$${latex_result}$$", "none", "white", interaction)

    except Exception as e:
        await interaction.response.send_message(f"無法計算傅立葉變換: {str(e)}")

@bot.slash_command(name="laplace", description="計算拉普拉斯變換或逆變換")
async def laplace_transform(interaction: nextcord.Interaction, function: str, transform_type: str = "forward"):
    try:
        t, s = sp.symbols('t s')
        expr = sp.sympify(function)

        if transform_type == "forward":
            lt = sp.laplace_transform(expr, t, s, noconds=True)
        elif transform_type == "inverse":
            lt = sp.inverse_laplace_transform(expr, s, t)
        else:
            raise ValueError("未知的拉普拉斯變換類型")

        latex_result = sp.latex(lt)
        await interaction.response.send_message(f"結果: $${latex_result}$$")
    except Exception as e:
        await interaction.response.send_message(f"無法計算拉普拉斯變換: {str(e)}")

@bot.slash_command(name="numpy", description="執行 NumPy 運算（僅限數學計算）")
async def numpy_calc(interaction: nextcord.Interaction, expression: str):
    unsafe_keywords = ["os", "sys", "import", "exec", "eval", "subprocess"]
    try:
        if any(keyword in expression for keyword in unsafe_keywords):
            raise ValueError("包含不允許的關鍵字")

        safe_globals = {"__builtins__": None, "np": np}
        safe_locals = {}
        result = eval(expression, safe_globals, safe_locals)

        await interaction.response.send_message(f"結果: `{result}`")
    except Exception as e:
        await interaction.response.send_message(f"無法執行 NumPy 表達式: {str(e)}")


# 啟動 bot
if __name__ == "__main__":
    bot.run(TOKEN)
