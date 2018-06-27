require "dev_dock/container"

module DevDock

	def self.start(name)
		container = DevDock::DevContainer.new(name)

		if not container.image.exist?
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
