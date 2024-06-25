from applications.ric_demo.simulation.src.ric_demo_environment import Environment_RIC


def main():
    env = Environment_RIC(visualization='babylon', webapp_config={'title': 'This is a title'})

    env.init()
    env.start()


if __name__ == '__main__':
    main()
