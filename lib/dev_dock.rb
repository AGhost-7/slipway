require "dev_dock/container"
require "dev_dock/log"

module DevDock

  def self.start(name)
    container = DevDock::DevContainer.new(name)

    if not container.image.exist?
      Log::info('image does not exist, pulling')
      container.image.pull
    end
    container.volumes.create

    container.run
  end

  def self.purge(name)
    container = DevDock::DevContainer.new(name)
    if container.exist?
      container.kill
    end
    container.volumes.remove
  end

end
