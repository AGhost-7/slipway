require 'fileutils'
require 'dev_dock/binds'

RSpec.describe DevDock::DevBinds do

  it 'remaps to the host' do
    home = ENV['DEV_DOCK_HOST_HOME'] || ENV['HOME']
    bind = DevDock::DevBinds.new([
      "#{File.join(ENV['HOME'],  '.ssh')}:/home/sample/.ssh"
    ]).list.first
    host_ssh = File.join(home, '.ssh')
    expect(bind.host_path).to eql(host_ssh)
  end

  it 'creates the file if it doesnt exist' do
    skip
  end

  it 'creates the directory if it doesnt exist' do
    skip
  end

  it 'doesnt explode if the file already exists' do
    test_directory = ENV['DEV_DOCK_TEST_DIR'] || File.join(Dir.pwd, '.test-dir')
    file_path = File.join(test_directory, 'foobar')

    FileUtils.rm_rf(test_directory)
    FileUtils.mkdir_p(test_directory)
    FileUtils.touch(file_path)
    DevDock::DevBind.new(nil, file_path, nil, nil).create()
  end

end
