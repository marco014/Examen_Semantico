from flask import Flask, request, render_template_string
import re
import ply.lex as lex

app = Flask(__name__)

# Definición de tokens para el analizador léxico
tokens = [
    'KEYWORD', 'ID', 'NUM', 'SYM', 'ERR'
]

t_KEYWORD = r'\b(int|DO|ENDDO|WHILE|ENDWHILE)\b'
t_ID = r'\b[a-zA-Z_][a-zA-Z_0-9]*\b'
t_NUM = r'\b\d+\b'
t_SYM = r'[;=()*+-]'
t_ERR = r'.'

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Carácter ilegal '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

# Plantilla HTML para mostrar resultados
html_template = '''
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {
            font-family: 'Arial', sans-serif;
            background-color: #222831;
            color: #eaeaea;
            margin: 0;
            padding: 20px;
        }
        h1 {
            text-align: center;
            color: #ff5722;
        }
        h2 {
            color: #ff5722;
        }
        form {
            margin-bottom: 20px;
            background-color: #393e46;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        form label {
            display: block;
            margin-bottom: 8px;
            color: #c5c6c7;
        }
        form textarea,
        form input[type="submit"] {
            padding: 10px;
            margin-bottom: 10px;
            border: none;
            border-radius: 20px;
            box-sizing: border-box;
        }
        form textarea {
            background-color: #222831;
            color: #eaeaea;
            border: 2px solid #ff5722;
            transition: border-color 0.3s;
            width: 80%;
            height: 150px;
            margin: 0 auto;
        }
        form textarea:focus {
            border-color: #ff784e;
        }
        form input[type="submit"] {
            background-color: #ff5722;
            color: #fff;
            cursor: pointer;
            transition: background-color 0.3s;
            width: 200px;
            margin: 0 auto;
            display: block;
        }
        form input[type="submit"]:hover {
            background-color: #ff784e;
        }
        .table-container {
            display: flex;
            justify-content: center;
            gap: 20px;
            flex-wrap: wrap;
        }
        table {
            width: 100%;
            max-width: 500px;
            border-collapse: collapse;
            margin-bottom: 20px;
            background-color: #393e46;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        table th, table td {
            border: 1px solid #ff5722;
            padding: 10px;
            text-align: left;
            color: #eaeaea;
        }
        th {
            background-color: #ff5722;
            color: #fff;
        }
        tr:nth-child(even) {
            background-color: #222831;
        }
        tr td:first-child,
        tr th:first-child {
            border-radius: 8px 0 0 8px;
        }
        tr td:last-child,
        tr th:last-child {
            border-radius: 0 8px 8px 0;
        }
        .error {
            color: #ff3b3b;
        }
    </style>
    <title>Analizador Léxico, Sintáctico y Semántico</title>
</head>
<body>
    <h1>Analizador Léxico, Sintáctico y Semántico</h1>
    <form method="POST">
        <label for="code">Ingresa el código aquí:</label><br>
        <textarea name="code" rows="6" cols="50">{{ code }}</textarea><br><br>
        <input type="submit" value="Ejecutar" name="action">
        <input type="submit" value="Borrar" name="action">
    </form>

    <div class="table-container">
        {% if lexical %}
        <div>
            <h2>Análisis Léxico</h2>
            <table>
                <tr>
                    <th>Token</th><th>PR</th><th>ID</th><th>Símbolo</th>
                </tr>
                {% for row in lexical %}
                <tr>
                    <td>{{ row[0] }}</td><td>{{ row[1] }}</td><td>{{ row[2] }}</td><td>{{ row[3] }}</td>
                </tr>
                {% endfor %}
                <tr>
                    <td>Total</td><td>{{ total['KEYWORD'] }}</td><td>{{ total['ID'] }}</td><td>{{ total['SYM'] }}</td>
                </tr>
            </table>
        </div>
        {% endif %}

        {% if syntactic or semantic %}
        <div>
            <h2>Análisis Sintáctico y Semántico</h2>
            <table>
                <tr>
                    <th>Sintáctico</th><th>Semántico</th>
                </tr>
                <tr>
                    <td>{{ syntactic }}</td><td>{{ semantic }}</td>
                </tr>
            </table>
        </div>
        {% endif %}
    </div>
</body>
</html>
'''

def analyze_lexical(code):
    lexer.input(code)
    results = {'KEYWORD': 0, 'ID': 0, 'SYM': 0}
    rows = []
    while True:
        tok = lexer.token()
        if not tok:
            break
        row = [''] * 4
        if tok.type == 'KEYWORD':
            results['KEYWORD'] += 1
            row[1] = 'x'
        elif tok.type == 'ID':
            results['ID'] += 1
            row[2] = 'x'
        elif tok.type == 'SYM':
            results['SYM'] += 1
            row[3] = 'x'
        row[0] = tok.value
        rows.append(row)
    return rows, results

def analyze_syntactic(code):
    errors = []
    do_count = 0
    while_count = 0
    within_do_block = False
    operation_in_block = False

    lines = code.split('\n')
    for i, line in enumerate(lines):
        stripped_line = line.strip()

        # Verificar la estructura básica de DO...ENDDO
        if stripped_line == 'DO':
            do_count += 1
            within_do_block = True
            operation_in_block = False
        elif stripped_line == 'ENDDO':
            if do_count <= 0:
                errors.append(f"ENDDO sin correspondiente DO en la línea {i + 1}.")
            else:
                do_count -= 1
            if not operation_in_block:
                errors.append(f"Bloque DO...ENDDO sin operaciones básicas en la línea {i + 1}.")
            within_do_block = False

        # Verificar que dentro de DO...ENDDO haya al menos una operación que termine con ;
        elif within_do_block and stripped_line and not stripped_line.startswith('DO') and not stripped_line.startswith('ENDDO'):
            if re.search(r'[+\-*/]', stripped_line) and stripped_line.endswith(';'):
                operation_in_block = True
            if not re.search(r'[+\-*/]', stripped_line):
                errors.append(f"Falta una operación básica en la línea {i + 1}: {line}")
            elif not stripped_line.endswith(';'):
                errors.append(f"Falta ; al final de la línea {i + 1}: {line}")

        # Verificar la estructura básica de WHILE...ENDWHILE
        elif stripped_line.startswith('WHILE'):
            while_count += 1
            if stripped_line.count('(') != stripped_line.count(')'):
                errors.append(f"Desbalance de paréntesis en la línea {i + 1}: {line}")
            # Verificar que la condición en el WHILE sea del tipo variable == valor
            condition = re.search(r'\((.*?)\)', stripped_line)
            if condition:
                condition = condition.group(1).strip()
                if not re.match(r'\w+\s*==\s*\d+', condition) and not re.match(r'int\s+\w+\s*==\s*\d+', condition):
                    errors.append(f"Condición en WHILE debe ser 'variable == valor' en la línea {i + 1}: {line}")
        elif stripped_line == 'ENDWHILE':
            if while_count <= 0:
                errors.append(f"ENDWHILE sin correspondiente WHILE en la línea {i + 1}.")
            else:
                while_count -= 1

        # Verificar la declaración de variables con punto y coma
        elif re.match(r'\bint\s+[a-zA-Z_][a-zA-Z_0-9]*\s*=\s*\d+\s*;', stripped_line):
            pass
        elif 'int' in stripped_line and not stripped_line.endswith(';'):
            errors.append(f"Declaración de variable mal formada en la línea {i + 1}: {line}")

    if do_count > 0:
        errors.append("DO sin correspondiente ENDDO.")
    if while_count > 0:
        errors.append("WHILE sin correspondiente ENDWHILE.")

    return " ".join(errors) if errors else ('Sintaxis correcta')

def analyze_semantic(code):
    errors = []

    declared_vars = set()
    lines = code.split('\n')

    for i, line in enumerate(lines):
        line = line.strip()

        # Verificar la inicialización de variables
        if re.match(r'\bint\s+[a-zA-Z_][a-zA-Z_0-9]*\s*=\s*\d+\s*;', line):
            var_name = line.split()[1].split('=')[0].strip()
            declared_vars.add(var_name)
        # Verificar el uso de variables antes de la declaración
        elif re.match(r'[a-zA-Z_][a-zA-Z_0-9]*\s*=\s*.*', line):
            var_name = line.split('=')[0].strip()
            if var_name not in declared_vars:
                errors.append(f"Variable {var_name} usada antes de ser declarada en la línea {i + 1}: {line}")
            else:
                # Verificar que todas las variables en el lado derecho de la asignación estén declaradas
                right_side_vars = re.findall(r'[a-zA-Z_][a-zA-Z_0-9]*', line.split('=')[1])
                for var in right_side_vars:
                    if var not in declared_vars and not var.isdigit():
                        errors.append(f"Variable {var} usada antes de ser declarada en la línea {i + 1}: {line}")

    if not errors:
        return "Uso correcto de las estructuras semánticas"
    else:
        return " ".join(errors)

@app.route('/', methods=['GET', 'POST'])
def index():
    code = ''
    lexical_results = []
    total_results = {'KEYWORD': 0, 'ID': 0, 'SYM': 0}
    syntactic_result = ''
    semantic_result = ''
    if request.method == 'POST':
        code = request.form['code']
        lexical_results, total_results = analyze_lexical(code)
        syntactic_result = analyze_syntactic(code)
        semantic_result = analyze_semantic(code)
    return render_template_string(html_template, code=code, lexical=lexical_results, total=total_results, syntactic=syntactic_result, semantic=semantic_result)

if __name__ == '__main__':
    app.run(debug=True)
