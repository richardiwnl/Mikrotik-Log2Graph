import datetime as date
import json
import re
import xlsxwriter

# Get the current day
current_day = date.datetime.now().strftime("%d-%m-%Y")

# The map between the static ip address and the person's name
ip_relationship = {
}

# Uses the config.json file to load the map between a person and its IPv4 address
try: 
    with open('config.json', 'r+') as config:
        try:
            json_ip_relationship = json.load(config)

            # Checks if the config file is empty
            if not json_ip_relationship:
                print('O arquivo de configuração está vazio. Saindo...')
                exit(-1)

            for person in json_ip_relationship:

                # Checks if a person's record is not empty and if they have an valid IPv4
                if not json_ip_relationship.get(person) or not re.match(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', json_ip_relationship[person].get('ip_address')):
                    print('Arquivo de configuração mal formatado. Saindo...')
                    exit(-1)

                json_ip_relationship[person].update({'visited_sites': []})

            ip_relationship = json_ip_relationship

        except json.JSONDecodeError:
            print('Não foi possível ler o arquivo de configuração')
            exit(-1)
except FileNotFoundError:
    print("Arquivo de configuração não encontrado. Saindo...")
    exit(-1)

try: 
    with open('tmplog.log', 'r+') as log_file:
        for line in log_file.readlines():
            match = re.search(
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b \b(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS) \bhttps?:\/\/[^\s]+\b', line)

            if match:
                # Get the IPv4 and URL for the matched regex
                ipv4_addr = match.group().split(' ')[0]
                site_url = match.group().split(' ')[2]

                for user in ip_relationship.values():
                    if user['ip_address'] == ipv4_addr:
                        all_urls = [list(record.values())[0]
                                    for record in user['visited_sites']]

                        if site_url not in all_urls:
                            user['visited_sites'].append(
                                {'url': site_url, 'visit_count': 1})
                        else:

                            [visited_site.update({'visit_count': visited_site['visit_count'] + 1})
                            for visited_site in user['visited_sites'] if visited_site['url'] == site_url]

except FileNotFoundError:
    print('O arquivo de logs não foi encontrado. Saindo...')
    exit(-1)

workbook = xlsxwriter.Workbook(
    f'Relatório de Acessos # {current_day}.xlsx')

for index, person in enumerate(ip_relationship):
    sites_array_len = len(ip_relationship[person]['visited_sites'])

    # Skips the creation of the worksheet if the user hasn't visited any websites
    if sites_array_len == 0:
        continue

    worksheet = workbook.add_worksheet(list(ip_relationship.keys())[index])

    worksheet.set_zoom(120)

    # Widen the table columns
    worksheet.set_column('A:A', 40)
    worksheet.set_column('B:B', 20)

    # Table header style
    header_style = workbook.add_format(
        {'bold': True, 'align': 'center', 'font_color': 'white', 'bg_color': '#538dd5'})

    # Create the table headers
    worksheet.write('A1', 'SITES', header_style)
    worksheet.write('B1', 'ACESSOS', header_style)

    url_style = workbook.add_format({'align': 'left'})
    visit_count_style = workbook.add_format({'align': 'center'})

    for index, site in enumerate(sorted(ip_relationship[person]['visited_sites'], key=lambda item: -item['visit_count'])):
        worksheet.write(f'A{index + 2}', site['url'], url_style)
        worksheet.write(f'B{index + 2}',
                        site['visit_count'], visit_count_style)

    chart = workbook.add_chart({'type': 'pie'})

    chart.set_title({'name': '10 SITES MAIS ACESSADOS'})
    chart.set_size({'width': 640, 'height': 400})

    chart.add_series({
        'values': f'=\'{person}\'!$B$2:$B${sites_array_len + 1 if sites_array_len <= 8 else 11}',
        'categories': f'=\'{person}\'!$A$2:$A${sites_array_len + 1 if sites_array_len <= 8 else 11}',
        'data_labels': {'percentage': True}
    })

    worksheet.insert_chart('C1', chart)

    worksheet.protect('fasouza021023')


# Tries to close the workbook
try:
    workbook.close()
except xlsxwriter.workbook.FileCreateError:
    print('Permissão negada. Não foi possível criar a planilha de relatórios')
    exit(-1)

print('Relatório de acesso gerado com sucesso!')
