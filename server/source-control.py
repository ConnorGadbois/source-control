import source_ctrl

if __name__ == '__main__':
    server = source_ctrl.A2Sserver(source_ctrl.config['address'], source_ctrl.config['port'])
    server.start()