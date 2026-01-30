import peewee
import yaml
from rich.table import Table
from rich.console import Console
from datetime import datetime
import time

with open('config.yml', 'r') as config_file:
    config = yaml.safe_load(config_file)

if config['database'] == 'postgresql':
    db = peewee.PostgresqlDatabase(config['postgresql']['db_name'], user=config['postgresql']['user'], host=config['postgresql']['host'], password=config['postgresql']['password'])
else:
    db = peewee.SqliteDatabase(config['sqlite']['db_path'], pragmas={'journal_mode': 'wal'})

class Task(peewee.Model):
    id = peewee.BigIntegerField(primary_key=True, unique=True, null=False)
    agent_ip = peewee.CharField(null=False)
    task = peewee.CharField(null=False)
    completed = peewee.BigIntegerField(default=0, null=False)

    class Meta:
        database = db
        db_table = 'tasks'

class Agent(peewee.Model):
    ip = peewee.CharField(null=False)
    checkins = peewee.BigIntegerField(default=0, null=False)
    last_checkin = peewee.BigIntegerField(null=False)
    tasks_sent = peewee.BigIntegerField(default=0, null=False)
    tags = peewee.CharField(null=False, default='')
    
    class Meta:
        database = db
        db_table = 'agents'

class Colors:
    RESET = '\033[0m'
    BLUE = '\033[94m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'

def print_banner() -> None:
    print(f'''                      
                                                                                                             {Colors.YELLOW}())))))))))))))))()){Colors.RESET} 
                                                                                                          {Colors.YELLOW}()))))))))))))))))))))))(){Colors.RESET} 
                                                                                                         {Colors.YELLOW}()))))     )))))))))))))))){Colors.RESET} 
.d88888b                                                   a88888b.                     dP                     dP      {Colors.YELLOW})))))))))))){Colors.RESET} 
88.    "'                                                 d8'   `88                     88                     88         {Colors.YELLOW}))))))))){Colors.RESET} 
`Y88888b. .d8888b. dP    dP 88d888b. .d8888b. .d8888b.    88        .d8888b. 88d888b. d8888P 88d888b. .d8888b. 88         {Colors.YELLOW})))))))){Colors.RESET} 
      `8b 88'  `88 88    88 88'  `88 88'  `"" 88ooood8    88        88'  `88 88'  `88   88   88'  `88 88'  `88 88          {Colors.YELLOW})))))/{Colors.RESET} 
d8'   .8P 88.  .88 88.  .88 88       88.  ... 88.  ...    Y8.   .88 88.  .88 88    88   88   88       88.  .88 88          {Colors.YELLOW}))))/{Colors.RESET} 
 Y88888P  `88888P' `88888P' dP       `88888P' `88888P'     Y88888P' `88888P' dP    dP   dP   dP       `88888P' dP         {Colors.YELLOW}))))/{Colors.RESET} 
                                                                                                                         {Colors.YELLOW})))({Colors.RESET} 
   Welcome to {Colors.YELLOW}Source Control{Colors.RESET} CLI                                                                                     {Colors.YELLOW}())))){Colors.RESET} 
   Use `{Colors.YELLOW}help{Colors.RESET}` for a list of commands
''')

def print_help() -> None:
    print(f'''
Commands:
    help                          -    Prints this menu

    agents                        -    List all agents
    agents {Colors.YELLOW}<tag>{Colors.RESET}                  -    List all agents with tag {Colors.YELLOW}<tag>{Colors.RESET}
    agents {Colors.YELLOW}<IP>{Colors.RESET}                   -    Get details about the agent with IP {Colors.YELLOW}<IP>{Colors.RESET}

    stats                         -    Prints statistics about the agents

    command {Colors.YELLOW}<IP|tag> <command>{Colors.RESET}    -    Send a command to the selected agents

    tag {Colors.YELLOW}<IP>{Colors.RESET} {Colors.YELLOW}<tag>{Colors.RESET}                -    Add a tag to the selected agent (Tags cannot contain spaces or commas)

    clear                         -    Clear the screen
    exit                          -    Exit the CLI
''')

def print_agents() -> None:
    table = Table()

    table.add_column('IP')
    table.add_column('Status')
    table.add_column('Checkins')
    table.add_column('Last Checkin')
    table.add_column('Tasks Sent')
    table.add_column('Tags')

    for agent in Agent.select():
        tags_string = ''

        for tag in agent.tags.split(','):
            if tag == 'linux':
                tags_string = tags_string + '[green]' + tag + '[/green]  '
            elif tag == 'windows':
                tags_string = tags_string + '[blue]' + tag + '[/blue]  '
            elif tag == 'bsd' or tag == 'pfsense':
                tags_string = tags_string + '[yellow]' + tag + '[/yellow]  '
            else:
                tags_string = tags_string + tag + ' '
        
        if time.time() - agent.last_checkin >= 600:
            table.add_row(agent.ip, '[red]Inactive[/red]', str(agent.checkins), str(datetime.fromtimestamp(agent.last_checkin)), str(agent.tasks_sent), tags_string)
        else:
            table.add_row(agent.ip, '[green]Active[/green]', str(agent.checkins), str(datetime.fromtimestamp(agent.last_checkin)), str(agent.tasks_sent), tags_string)

    Console().print(table)

def print_agents_by_tag_or_ip(search_str: str) -> None:
    table = Table()

    table.add_column('IP')
    table.add_column('Status')
    table.add_column('Checkins')
    table.add_column('Last Checkin')
    table.add_column('Tasks Sent')
    table.add_column('Tags')

    for agent in Agent.select():
        tags_string = ''

        for tag in agent.tags.split(','):
            if tag == 'linux':
                tags_string = tags_string + '[green]' + tag + '[/green]  '
            elif tag == 'windows':
                tags_string = tags_string + '[blue]' + tag + '[/blue]  '
            elif tag == 'bsd' or tag == 'pfsense':
                tags_string = tags_string + '[yellow]' + tag + '[/yellow]  '
            else:
                tags_string = tags_string + tag + ' '

        if search_str in agent.tags.split(',') or agent.ip == search_str:
            if time.time() - agent.last_checkin >= config['inactive_time']:
                table.add_row(agent.ip, '[red]Inactive[/red]', str(agent.checkins), str(datetime.fromtimestamp(agent.last_checkin)), str(agent.tasks_sent), tags_string)
            else:
                table.add_row(agent.ip, '[green]Active[/green]', str(agent.checkins), str(datetime.fromtimestamp(agent.last_checkin)), str(agent.tasks_sent), tags_string)

    Console().print(table)

def print_status() -> None:
    total_agents = len(Agent.select())
    active_agents = len(Agent.select().where(Agent.last_checkin >= time.time() - config['inactive_time']))
    inactive_agents = len(Agent.select().where(Agent.last_checkin < time.time() - config['inactive_time']))
    total_tasks = len(Task.select())
    completed_tasks = len(Task.select().where(Task.completed == 1))

    print(f'''
Total Agents: {total_agents}
Active Agents: {Colors.GREEN}{active_agents}{Colors.RESET}
Inactive Agents: {Colors.RED}{inactive_agents}{Colors.RESET}
Total Tasks: {total_tasks}
Completed Tasks: {completed_tasks}
''')

def ip_match(ip: str, pattern: str):
    return(all(p == '*' or x == p for x, p in zip(ip.split('.'), pattern.split('.'))))

def is_agent(agent_ip: str) -> bool:
    return(len(Agent.select().where(Agent.ip == agent_ip)) != 0)

def select_agents(search_str: str) -> list:
    agents = []

    query = Agent.select()

    for agent in query:
        if ip_match(agent.ip, search_str) or search_str in agent.tags:
            agents.append(agent)

    return(agents)

def send_command(search_str: str, command: str) -> None:
    agents = select_agents(search_str)
    commands_sent = 0

    for agent in agents:
        Task.create(agent_ip = agent.ip, task = command, completed = False)
        commands_sent += 1

    print(f'Sent the command to {Colors.YELLOW}{commands_sent}{Colors.RESET} agents')

def add_tag(ip_pattern: str, tag: str) -> None:
    updated_agents = 0
    
    for agent in Agent.select():
        if ip_match(agent.ip, ip_pattern):
            current_tags = agent.tags

            if tag in current_tags[0].split(','):
                print(f'{Colors.YELLOW}{agent.ip}{Colors.RESET} already has the tag {Colors.YELLOW}{tag}{Colors.RESET}.')
                return

            if current_tags[0] == '':
                Agent.update(tags=str(tag)).where(Agent.ip == agent.ip).execute()
            else:
                Agent.update(tags=Agent.tags.concat(',' + str(tag))).where(Agent.ip == agent.ip).execute()

            updated_agents += 1

    print(f'Tagged {Colors.YELLOW}{updated_agents}{Colors.RESET} with {Colors.YELLOW}{tag}{Colors.RESET}')

def main():
    if config['print_banner']:
        print_banner()

    while True:
        try:
            user_command = input('SC> ').split(' ')

            match user_command[0]:
                case 'help':
                    print_help()

                case 'clear':
                    print('\x1b[2J\x1b[H')

                case 'agents':
                    if len(user_command) < 2:
                        print_agents()
                    else:
                        print_agents_by_tag_or_ip(user_command[1])

                case 'stats':
                    print_status()

                case 'command':
                    if len(user_command) < 2:
                        print(f'\nUsage:\n\tcommand {Colors.YELLOW}<IP|tag> <command>{Colors.RESET}    -    Send a command to the selected agents\n')
                    else:
                        send_command(user_command[1], ' '.join(user_command[2:]))

                case 'tag':
                    if len(user_command) < 3:
                        print(f'\nUsage:\n\ttag {Colors.YELLOW}<IP Regex>{Colors.RESET} {Colors.YELLOW}<tag>{Colors.RESET}          -    Add a tag to the selected agent (Tags cannot contain spaces or commas)\n')
                    else:
                        if ',' in user_command[2]:
                            print(f'{Colors.RED}Tags cannot contain commas.{Colors.RESET}')

                        else:
                            add_tag(user_command[1], user_command[2])

                case 'exit':
                    print(f'{Colors.YELLOW}Goodbye!{Colors.RESET}')
                    quit(0)

        except KeyboardInterrupt:
            print('')

if __name__ == '__main__':
    main()
