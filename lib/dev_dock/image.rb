require 'docker'

module DevDock

  class DevImage

    def initialize(name)
      @name = name
      @container_config = nil
    end

    def name
      @name
    end

    def exist?
      Docker::Image::exist?(@name)
    end

    def pull
      # for some reason pulling images isn't part of the api?
      `docker pull #{name}`
    end

    def container_config
      if @container_config.nil?
        image = Docker::Image.get(@name)
        @container_config = image.json['ContainerConfig']
      end
      @container_config
    end

    def user
      return container_config['User']
    end

  end
end
