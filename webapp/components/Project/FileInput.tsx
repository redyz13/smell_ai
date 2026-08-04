import React, { useEffect, useRef } from "react";

type FileInputProps = {
  onChange: (event: React.ChangeEvent<HTMLInputElement>) => void;
};

const FileInput: React.FC<FileInputProps> = ({ onChange }) => {
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    if (fileInputRef.current) {
      fileInputRef.current.webkitdirectory = true;
    }
  }, []);

  return (
    <input
      ref={fileInputRef}
      type="file"
      onChange={onChange}
      className="w-full px-4 py-3 bg-gray-50 border border-gray-300 rounded-lg cursor-pointer hover:bg-gray-100 transition-all duration-300"
      multiple
      data-testid="file-input"
    />
  );
};

export default FileInput;
